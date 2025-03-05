/**
 * py-dem-bones 文档自定义 JavaScript
 */

// 等待文档加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 为代码块添加复制按钮
    addCopyButtonsToCodeBlocks();
    
    // 移除目录中多余的小三角形图标
    // 移除所有展开/折叠图标
    const expandIcons = document.querySelectorAll('.toctree-expand');
    expandIcons.forEach(function(icon) {
        icon.style.display = 'none';
        icon.parentNode.classList.remove('current');
    });
    
    // 移除相关的展开/折叠功能
    const toctreeItems = document.querySelectorAll('.toctree-l1, .toctree-l2, .toctree-l3');
    toctreeItems.forEach(function(item) {
        const childList = item.querySelector('ul');
        if (childList) {
            childList.style.display = 'block';
        }
    });
    
    // 添加目录折叠功能
    addTocCollapsible();
    
    // 添加暗色/亮色模式切换
    setupThemeToggle();
    
    // 添加搜索结果增强
    enhanceSearchResults();
    
    // 添加API文档交互
    enhanceApiDocs();
    
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

// 为目录链接添加点击事件
const toctreeLinks = document.querySelectorAll('.toctree-wrapper a');
toctreeLinks.forEach(function(link) {
    link.addEventListener('click', function(e) {
        // 移除所有链接的激活状态
        toctreeLinks.forEach(function(l) {
            l.classList.remove('active');
        });
        // 添加激活状态到当前链接
        this.classList.add('active');
    });
});

/**
 * 为代码块添加复制按钮
 */
function addCopyButtonsToCodeBlocks() {
    // 查找所有代码块
    const codeBlocks = document.querySelectorAll('pre');
    
    codeBlocks.forEach(function(codeBlock) {
        // 创建复制按钮
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Copy';
        
        // 添加样式
        copyButton.style.position = 'absolute';
        copyButton.style.right = '0.5em';
        copyButton.style.top = '0.5em';
        copyButton.style.padding = '0.3em 0.6em';
        copyButton.style.background = 'var(--pdb-primary-color)';
        copyButton.style.color = 'white';
        copyButton.style.border = 'none';
        copyButton.style.borderRadius = '3px';
        copyButton.style.fontSize = '0.8em';
        copyButton.style.cursor = 'pointer';
        copyButton.style.opacity = '0';
        copyButton.style.transition = 'opacity 0.2s';
        
        // 设置代码块为相对定位，以便正确放置按钮
        codeBlock.style.position = 'relative';
        
        // 添加按钮到代码块
        codeBlock.appendChild(copyButton);
        
        // 鼠标悬停时显示按钮
        codeBlock.addEventListener('mouseenter', function() {
            copyButton.style.opacity = '1';
        });
        
        codeBlock.addEventListener('mouseleave', function() {
            copyButton.style.opacity = '0';
        });
        
        // 点击按钮复制代码
        copyButton.addEventListener('click', function() {
            const code = codeBlock.querySelector('code') ? 
                codeBlock.querySelector('code').textContent : 
                codeBlock.textContent;
            
            navigator.clipboard.writeText(code).then(function() {
                // 复制成功，临时改变按钮文本
                copyButton.textContent = 'Copied!';
                setTimeout(function() {
                    copyButton.textContent = 'Copy';
                }, 2000);
            }).catch(function(err) {
                console.error('Failed to copy: ', err);
                copyButton.textContent = 'Error!';
                setTimeout(function() {
                    copyButton.textContent = 'Copy';
                }, 2000);
            });
        });
    });
}

/**
 * 添加目录折叠功能
 */
function addTocCollapsible() {
    const tocTree = document.querySelector('.toctree-wrapper');
    if (!tocTree) return;
    
    // 为每个一级列表项添加折叠功能
    const topLevelItems = tocTree.querySelectorAll('li.toctree-l1');
    
    topLevelItems.forEach(function(item) {
        const sublist = item.querySelector('ul');
        if (!sublist) return;
        
        // 创建折叠按钮
        const toggleButton = document.createElement('span');
        toggleButton.className = 'toc-toggle';
        toggleButton.innerHTML = '▼';
        toggleButton.style.cursor = 'pointer';
        toggleButton.style.marginRight = '0.5em';
        toggleButton.style.fontSize = '0.8em';
        toggleButton.style.transition = 'transform 0.2s';
        
        // 将按钮添加到列表项的链接前面
        const link = item.querySelector('a');
        link.parentNode.insertBefore(toggleButton, link);
        
        // 添加点击事件
        toggleButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // 切换子列表的显示状态
            if (sublist.style.display === 'none') {
                sublist.style.display = '';
                toggleButton.innerHTML = '▼';
                toggleButton.style.transform = 'rotate(0deg)';
            } else {
                sublist.style.display = 'none';
                toggleButton.innerHTML = '▶';
                toggleButton.style.transform = 'rotate(-90deg)';
            }
        });
    });
}

/**
 * 设置主题切换功能
 */
function setupThemeToggle() {
    // 检查是否已有主题切换按钮
    if (document.querySelector('.theme-toggle-button')) return;
    
    // 创建主题切换按钮
    const toggleButton = document.createElement('button');
    toggleButton.className = 'theme-toggle-button';
    toggleButton.innerHTML = '🌓';
    toggleButton.title = 'Toggle Light/Dark Mode';
    
    // 设置按钮样式
    toggleButton.style.position = 'fixed';
    toggleButton.style.bottom = '20px';
    toggleButton.style.right = '20px';
    toggleButton.style.width = '40px';
    toggleButton.style.height = '40px';
    toggleButton.style.borderRadius = '50%';
    toggleButton.style.background = 'var(--pdb-primary-color)';
    toggleButton.style.color = 'white';
    toggleButton.style.border = 'none';
    toggleButton.style.fontSize = '1.2em';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.zIndex = '1000';
    toggleButton.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
    
    // 添加到文档
    document.body.appendChild(toggleButton);
    
    // 检查当前主题
    const currentTheme = localStorage.getItem('theme') || 'auto';
    if (currentTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else if (currentTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    }
    
    // 添加点击事件
    toggleButton.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'auto';
        let newTheme;
        
        if (currentTheme === 'auto' || currentTheme === 'light') {
            newTheme = 'dark';
            toggleButton.innerHTML = '🌞';
        } else {
            newTheme = 'light';
            toggleButton.innerHTML = '🌙';
        }
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

/**
 * 增强搜索结果显示
 */
function enhanceSearchResults() {
    // 等待搜索结果加载
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // 检查是否是搜索结果
                const searchResults = document.querySelector('.search-results');
                if (searchResults) {
                    // 为每个搜索结果添加高亮和预览
                    const results = searchResults.querySelectorAll('li');
                    results.forEach(function(result) {
                        const link = result.querySelector('a');
                        if (!link) return;
                        
                        // 添加鼠标悬停效果
                        result.style.transition = 'background-color 0.2s';
                        result.addEventListener('mouseenter', function() {
                            result.style.backgroundColor = 'var(--pdb-light-bg)';
                        });
                        result.addEventListener('mouseleave', function() {
                            result.style.backgroundColor = '';
                        });
                    });
                }
            }
        });
    });
    
    // 开始观察文档变化
    observer.observe(document.body, { childList: true, subtree: true });
}

/**
 * 增强API文档交互
 */
function enhanceApiDocs() {
    // 查找所有API文档项
    const apiItems = document.querySelectorAll('dl.class, dl.function, dl.method');
    
    apiItems.forEach(function(item) {
        // 获取标题
        const title = item.querySelector('dt');
        if (!title) return;
        
        // 添加折叠功能
        title.style.cursor = 'pointer';
        
        // 获取内容
        const content = item.querySelector('dd');
        if (!content) return;
        
        // 添加点击事件
        title.addEventListener('click', function(e) {
            // 如果点击的是链接，不触发折叠
            if (e.target.tagName === 'A') return;
            
            // 切换内容显示状态
            if (content.style.display === 'none') {
                content.style.display = 'block';
                title.classList.remove('collapsed');
            } else {
                content.style.display = 'none';
                title.classList.add('collapsed');
            }
        });
    });
}
