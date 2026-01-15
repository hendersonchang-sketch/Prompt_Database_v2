/**
 * BananaDB Content Script
 * 負責在網頁中顯示 Prompt 輸入對話框
 */

// 監聽來自 background script 的訊息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'showPromptDialog') {
        showPromptInputDialog(request.imageUrl, request.pageUrl);
        sendResponse({ received: true });
    }
});

/**
 * 顯示 Prompt 輸入對話框
 */
function showPromptInputDialog(imageUrl, pageUrl) {
    // 檢查是否已存在對話框，避免重複建立
    if (document.getElementById('bananadb-dialog')) {
        return;
    }

    // 建立遮罩層
    const overlay = document.createElement('div');
    overlay.id = 'bananadb-dialog';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 999999;
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    `;

    // 建立對話框
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        background: #1a1a1a;
        border-radius: 12px;
        padding: 24px;
        width: 90%;
        max-width: 600px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        color: #ffffff;
    `;

    dialog.innerHTML = `
        <h2 style="margin: 0 0 16px 0; color: #FFD700; font-size: 24px;">
            🍌 儲存至 BananaDB
        </h2>
        <p style="margin: 0 0 16px 0; color: #999; font-size: 14px;">
            請輸入或貼上圖片的原始 Prompt（選填）
        </p>
        
        <div style="margin-bottom: 16px;">
            <label style="display: block; margin-bottom: 8px; color: #ccc; font-size: 14px;">
                原始 Prompt：
            </label>
            <textarea 
                id="bananadb-prompt-input"
                placeholder="貼上或輸入 prompt（可選）"
                style="
                    width: 100%;
                    min-height: 120px;
                    padding: 12px;
                    background: #2a2a2a;
                    border: 1px solid #444;
                    border-radius: 8px;
                    color: #fff;
                    font-size: 14px;
                    resize: vertical;
                    box-sizing: border-box;
                "
            ></textarea>
        </div>
        
        <div style="margin-bottom: 16px;">
            <label style="display: flex; align-items: center; color: #ccc; font-size: 14px; cursor: pointer;">
                <input 
                    type="checkbox" 
                    id="bananadb-skip-ai-checkbox"
                    style="margin-right: 8px; width: 18px; height: 18px; cursor: pointer;"
                >
                <span>直接使用此 Prompt（跳過 AI 分析）</span>
            </label>
        </div>
        
        <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button 
                id="bananadb-cancel-btn"
                style="
                    padding: 10px 24px;
                    background: #444;
                    border: none;
                    border-radius: 6px;
                    color: #fff;
                    font-size: 14px;
                    cursor: pointer;
                    transition: background 0.2s;
                "
            >取消</button>
            <button 
                id="bananadb-save-btn"
                style="
                    padding: 10px 24px;
                    background: #FFD700;
                    border: none;
                    border-radius: 6px;
                    color: #000;
                    font-weight: bold;
                    font-size: 14px;
                    cursor: pointer;
                    transition: background 0.2s;
                "
            >儲存至 BananaDB</button>
        </div>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    // 焦點到 textarea
    const textarea = document.getElementById('bananadb-prompt-input');
    textarea.focus();

    // 按鈕事件
    document.getElementById('bananadb-cancel-btn').addEventListener('click', () => {
        overlay.remove();
    });

    document.getElementById('bananadb-save-btn').addEventListener('click', () => {
        const promptText = textarea.value.trim();
        const skipAI = document.getElementById('bananadb-skip-ai-checkbox').checked;

        // 傳送到 background script
        chrome.runtime.sendMessage({
            action: 'saveImage',
            imageUrl: imageUrl,
            pageUrl: pageUrl,
            promptText: promptText,
            skipAI: skipAI
        });

        overlay.remove();
    });

    // 點擊遮罩層關閉
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
        }
    });

    // ESC 鍵關閉
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            overlay.remove();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}
