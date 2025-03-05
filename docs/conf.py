# -- Import mock modules for examples -----------------------------------------
import os
import sys

# 添加项目根目录到Python路径，以便导入模块
sys.path.insert(0, os.path.abspath('.'))

# 设置模板目录
templates_path = ['_templates']

# 设置静态文件目录
html_static_path = ['_static']

# 导入模拟模块，用于处理示例中的导入
try:
    import py_dem_bones
except ImportError:
    # 如果无法导入实际模块，使用模拟模块
    import sys
    from unittest.mock import MagicMock

    class MockDemBones:
        """Mock DemBones class for documentation."""
        
        def __init__(self):
            """Initialize DemBones."""
            self.nIters = 20
            self.nInitIters = 10
            self.nTransIters = 5
            self.nWeightsIters = 3
            self.nnz = 4
            self.weightsSmooth = 1e-4
            self.nV = 0
            self.nB = 0
            self.nF = 0
    
    class MockModule(MagicMock):
        """Mock module for sphinx-gallery."""
        
        @classmethod
        def __getattr__(cls, name):
            if name == "DemBones":
                return MockDemBones
            return MagicMock()
    
    # Add mock modules
    MOCK_MODULES = ['py_dem_bones', 'py_dem_bones._py_dem_bones']
    for mod_name in MOCK_MODULES:
        sys.modules[mod_name] = MockModule()

# -- Project information -----------------------------------------------------
project = 'py-dem-bones'
copyright = '2024, Long Hao'
author = 'Long Hao'

# The full version, including alpha/beta/rc tags
release = '0.4.0'

# 主要版本
version = '0.4.0'

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "myst_parser",
    "py_dem_bones_sphinxext",  # 添加我们的自定义扩展
]

# 如果设置了 Google Analytics ID，则添加 Google Analytics 扩展
google_analytics_id = os.environ.get("GOOGLE_ANALYTICS_ID")
if google_analytics_id:
    extensions.append("sphinxcontrib.googleanalytics")
    googleanalytics_id = google_analytics_id
    googleanalytics_enabled = True

# 模拟导入的模块列表，用于避免导入错误
autodoc_mock_imports = [
    'numpy', 
    'pandas', 
    'matplotlib', 
    'scipy',
    'cv2',
    'PIL',
    'imageio',
    'skimage',
    'torch',
    'tensorflow',
    'itk',  # Add 'itk' to the list
    'vtk',  # Add 'vtk' to the list
]

autodoc_typehints = 'none'
autodoc_import_mock = True

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# 指定 myst 解析器配置
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    "sidebar_hide_name": False,
    "light_css_variables": {
        "color-brand-primary": "#2980b9",
        "color-brand-content": "#3498db",
        "color-admonition-background": "#f8f9fa",
        "font-stack": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif",
        "font-stack--monospace": "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace",
        "color-background-primary": "#ffffff",
        "color-background-secondary": "#f8f9fa",
        "color-foreground-primary": "#333333",
        "color-foreground-secondary": "#5a5a5a",
        "color-announcement-background": "#2980b9",
        "color-announcement-text": "#ffffff",
        "color-link": "#3498db",
        "color-link--hover": "#e74c3c",
        "color-inline-code-background": "#f5f7f9",
    },
    "dark_css_variables": {
        "color-brand-primary": "#3498db",
        "color-brand-content": "#2980b9",
        "color-admonition-background": "#2d333b",
        "color-background-primary": "#1a1a1a",
        "color-background-secondary": "#2d333b",
        "color-foreground-primary": "#f0f0f0",
        "color-foreground-secondary": "#aaaaaa",
        "color-announcement-background": "#3498db",
        "color-announcement-text": "#ffffff",
        "color-link": "#3498db",
        "color-link--hover": "#e74c3c",
        "color-inline-code-background": "#22272e",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/loonghao/py-dem-bones",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
    "navigation_with_keys": True,
    "announcement": "This is a beta version of the documentation. Content may change.",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
html_sidebars = {
    "**": ["sidebar/brand.html", "sidebar/search.html", "sidebar/scroll-start.html", 
           "sidebar/navigation.html", "sidebar/scroll-end.html"],
}

# 添加自定义 CSS 和 JS 文件
html_css_files = ["custom.css"]
html_js_files = ["custom.js"]

# 设置项目徽标
html_logo = "_static/logo-dark.png"
html_favicon = "_static/logo-dark.png"

autodoc_class_signature = 'separated'
autodoc_member_order = 'bysource'
autodoc_inherit_docstrings = True
autodoc_default_options = {
    "show-inheritance": True,
    "undoc-members": True,
    "inherited-members": True,
}

# -- Extension configuration -------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Options for intersphinx extension ---------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable', None),
}

# -- Options for autodoc extension ------------------------------------------
autodoc_member_order = 'bysource'

# -- Options for myst_parser extension --------------------------------------
# 这些配置会被 myst-nb 使用
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

# 避免与 myst-nb 冲突的配置
myst_update_mathjax = False  # 让 myst-nb 处理数学公式
myst_heading_anchors = 3

# 添加 stubs 目录到 Python 路径，以便 autodoc 可以找到类型提示文件
stubs_dir = os.path.join(os.path.abspath('..'), 'src', 'py_dem_bones-stubs')
if os.path.exists(stubs_dir):
    sys.path.insert(0, stubs_dir)

# 尝试导入模块，如果失败则不会影响文档构建
try:
    import py_dem_bones
except ImportError:
    print("Warning: Failed to import py_dem_bones module. API documentation may be incomplete.")
