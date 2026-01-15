/**
 * BananaDB Collector - Chrome Extension Background Script
 * 
 * 功能：建立右鍵選單，將圖片傳送至本地 BananaDB 伺服器
 */

// 本地 API 端點
const API_BASE_URL = 'http://localhost:8000';

// 建立右鍵選單
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: 'saveToBananaDB',
        title: '🍌 Save to BananaDB',
        contexts: ['image']
    });

    console.log('✅ BananaDB Collector 已安裝');
});

// 監聽右鍵選單點擊事件
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId === 'saveToBananaDB') {
        try {
            // 提取圖片 URL
            const imageUrl = info.srcUrl;

            if (!imageUrl) {
                showNotification('❌ 錯誤', '無法取得圖片 URL');
                return;
            }

            // 取得頁面 URL
            const pageUrl = tab.url || '';

            console.log('📤 準備儲存圖片:', { imageUrl, pageUrl });

            // 注入 content script 並顯示對話框
            try {
                await chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    files: ['content.js']
                });
            } catch (e) {
                console.log('Content script already injected or injection failed:', e);
            }

            // 發送訊息到 content script 顯示對話框
            chrome.tabs.sendMessage(tab.id, {
                action: 'showPromptDialog',
                imageUrl: imageUrl,
                pageUrl: pageUrl
            });

        } catch (error) {
            console.error('❌ 處理失敗:', error);
            showNotification('❌ 錯誤', error.message || '處理失敗');
        }
    }
});

// 監聽來自 content script 的儲存請求
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'saveImage') {
        handleSaveImage(request.imageUrl, request.pageUrl, request.promptText, request.skipAI);
        sendResponse({ received: true });
    }
    return true;
});

/**
 * 處理儲存圖片
 */
async function handleSaveImage(imageUrl, pageUrl, promptText, skipAI) {
    try {
        console.log('💾 開始儲存:', { imageUrl, pageUrl, promptText, skipAI });

        // 發送至 BananaDB API
        const response = await fetch(`${API_BASE_URL}/api/collect_url`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_url: imageUrl,
                page_url: pageUrl,
                context_text: promptText,
                skip_ai: skipAI || false
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();

        // 顯示成功通知
        showNotification(
            '✅ 儲存成功',
            `圖片已新增至 BananaDB (ID: ${result.data.image_id})`
        );

        console.log('✅ 儲存成功:', result);

    } catch (error) {
        console.error('❌ 儲存失敗:', error);

        // 顯示錯誤通知
        showNotification(
            '❌ 儲存失敗',
            error.message || '請確認 BananaDB 伺服器正在執行 (http://localhost:8000)'
        );
    }
}

/**
 * 顯示通知
 * @param {string} title - 通知標題
 * @param {string} message - 通知訊息
 */
function showNotification(title, message) {
    chrome.notifications.create({
        type: 'basic',
        iconUrl: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="75" font-size="75">🍌</text></svg>',
        title: title,
        message: message,
        priority: 2
    });
}

// 監聽來自 content script 的訊息（預留擴充功能）
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('收到訊息:', request);
    sendResponse({ received: true });
});
