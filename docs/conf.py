# -- Import mock modules for examples -----------------------------------------
import os
import sys

# 添加项目根目录到Python路径，以便导入模块
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../src'))

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
release = '0.3.0'

# 主要版本
version = '0.3.0'

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "myst_parser",
]

# 只在有 Google Analytics ID 时启用 GA 扩展
import os
googleanalytics_id = os.environ.get('GOOGLE_ANALYTICS_ID', '')
if googleanalytics_id:
    extensions.append("sphinxcontrib.googleanalytics")
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
html_theme = 'furo'
html_theme_options = {
    'light_logo': 'logo-light.svg',
    'dark_logo': 'logo-dark.svg',
    'sidebar_hide_name': True,
}
html_css_files = [
    'custom.css',
]
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
