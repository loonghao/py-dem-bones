/**
 * Custom JavaScript for py-dem-bones documentation
 * Adds expandable code snippets to the example gallery
 */

document.addEventListener('DOMContentLoaded', function() {
    // 为每个示例卡片添加展开代码的功能
    const exampleCards = document.querySelectorAll('.sphx-glr-thumbcontainer');
    
    exampleCards.forEach(function(card) {
        // 创建展开按钮
        const expandButton = document.createElement('button');
        expandButton.className = 'example-expand-button';
        expandButton.innerHTML = '<span>查看代码</span>';
        card.appendChild(expandButton);
        
        // 创建代码容器
        const codeContainer = document.createElement('div');
        codeContainer.className = 'example-code-container';
        codeContainer.style.display = 'none';
        
        // 获取示例链接
        const exampleLink = card.querySelector('a');
        const exampleUrl = exampleLink ? exampleLink.href : null;
        
        if (exampleUrl) {
            // 添加点击事件
            expandButton.addEventListener('click', function() {
                if (codeContainer.style.display === 'none') {
                    // 如果代码容器是空的，则获取代码
                    if (codeContainer.innerHTML === '') {
                        expandButton.innerHTML = '<span>加载中...</span>';
                        
                        // 获取示例代码
                        fetch(exampleUrl)
                            .then(response => response.text())
                            .then(html => {
                                // 提取代码部分
                                const parser = new DOMParser();
                                const doc = parser.parseFromString(html, 'text/html');
                                const codeBlocks = doc.querySelectorAll('.highlight-python');
                                
                                if (codeBlocks.length > 0) {
                                    // 创建代码片段
                                    const codeFragment = document.createDocumentFragment();
                                    
                                    // 添加标题
                                    const title = document.createElement('h4');
                                    title.textContent = '源代码';
                                    codeFragment.appendChild(title);
                                    
                                    // 添加代码
                                    codeBlocks.forEach(block => {
                                        codeFragment.appendChild(block.cloneNode(true));
                                    });
                                    
                                    // 添加到容器
                                    codeContainer.appendChild(codeFragment);
                                    
                                    // 显示代码
                                    codeContainer.style.display = 'block';
                                    expandButton.innerHTML = '<span>隐藏代码</span>';
                                } else {
                                    codeContainer.innerHTML = '<p>无法加载代码，请点击标题查看完整示例。</p>';
                                    codeContainer.style.display = 'block';
                                    expandButton.innerHTML = '<span>隐藏</span>';
                                }
                            })
                            .catch(error => {
                                console.error('Error fetching example code:', error);
                                codeContainer.innerHTML = '<p>加载代码时出错，请点击标题查看完整示例。</p>';
                                codeContainer.style.display = 'block';
                                expandButton.innerHTML = '<span>隐藏</span>';
                            });
                    } else {
                        // 如果已经加载过代码，直接显示
                        codeContainer.style.display = 'block';
                        expandButton.innerHTML = '<span>隐藏代码</span>';
                    }
                } else {
                    // 隐藏代码
                    codeContainer.style.display = 'none';
                    expandButton.innerHTML = '<span>查看代码</span>';
                }
            });
            
            // 添加代码容器到卡片
            card.appendChild(codeContainer);
        }
    });
});
