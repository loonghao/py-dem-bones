# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------
project = 'py-dem-bones'
copyright = '2025, Long Hao'
author = 'Long Hao'

# The full version, including alpha/beta/rc tags
release = '0.1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo'
html_static_path = ['_static']

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
autodoc_typehints = 'description'

# 添加项目根目录到Python路径，以便导入模块
import os
import sys

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../src'))

# 添加 stubs 目录到 Python 路径，以便 autodoc 可以找到类型提示文件
stubs_dir = os.path.join(os.path.abspath('..'), 'src', 'py_dem_bones-stubs')
if os.path.exists(stubs_dir):
    sys.path.insert(0, stubs_dir)

# 尝试导入模块，如果失败则不会影响文档构建
try:
    import py_dem_bones
except ImportError:
    print("Warning: Failed to import py_dem_bones module. API documentation may be incomplete.")

# 告诉 sphinx 在 HTML 构建中包含生成的内容
html_sidebars = {
    '**': ['sidebar/brand.html', 'sidebar/search.html', 'sidebar/scroll-start.html',
           'sidebar/navigation.html', 'sidebar/ethical-ads.html', 'sidebar/scroll-end.html']
}
