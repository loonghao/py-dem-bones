import os
import re
import sys
import typing
import sphinx.util.nodes
import inspect
import sphinx.environment

import docutils.nodes
import sphinx.application
import sphinx.util.logging
import sphinx.util.docutils
import docutils.statemachine
from docutils.parsers.rst import directives, Directive
from docutils import nodes

_LOG = sphinx.util.logging.getLogger(f"ext.py_dem_bones")


class PyDemBonesAPIDirective(sphinx.util.docutils.SphinxDirective):
    """
    Special directive for generating API documentation for py-dem-bones.
    """
    required_arguments = 0
    optional_arguments = 0

    def run(self) -> list[docutils.nodes.Node]:
        # Create the node
        node = docutils.nodes.section()
        node.document = self.state.document

        rst = docutils.statemachine.ViewList()

        # Add the extension file as a dependency
        self.env.note_dependency(__file__)

        path, line_number = self.get_source_info()

        # Generate API documentation
        api_rst = self.generate_api_rst()

        # Add each line to the view list
        for index, line in enumerate(api_rst):
            # Note: "line" has to be a single line! It can't be a line like "this\nthat".
            rst.append(line, path, line_number + index)

        # Convert the rst into the appropriate docutils/sphinx nodes
        sphinx.util.nodes.nested_parse_with_titles(self.state, rst, node)

        # Return the generated nodes
        return node.children

    def generate_api_rst(self) -> list[str]:
        """
        Generate reStructuredText for the py-dem-bones API.
        """
        rst = []

        # Try to import the module
        try:
            import py_dem_bones
        except ImportError:
            rst.append(".. warning:: Failed to import py_dem_bones module. API documentation may be incomplete.")
            rst.append("")
            return rst

        # Add module documentation
        rst.append("Module: py_dem_bones")
        rst.append("====================")
        rst.append("")
        
        if py_dem_bones.__doc__:
            rst.append(py_dem_bones.__doc__)
        rst.append("")

        # Document main classes
        rst.append("Classes")
        rst.append("-------")
        rst.append("")

        # Get all classes from the module
        for name, obj in inspect.getmembers(py_dem_bones):
            if inspect.isclass(obj) and obj.__module__.startswith('py_dem_bones'):
                rst.append(f".. py:class:: {name}")
                rst.append("")
                
                if obj.__doc__:
                    for line in obj.__doc__.split('\n'):
                        rst.append(f"   {line}")
                    rst.append("")
                
                # Document methods
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if not method_name.startswith('_') or method_name == '__init__':
                        rst.append(f"   .. py:method:: {method_name}{inspect.signature(method)}")
                        rst.append("")
                        
                        if method.__doc__:
                            for line in method.__doc__.split('\n'):
                                rst.append(f"      {line}")
                            rst.append("")

        # Document functions
        rst.append("Functions")
        rst.append("---------")
        rst.append("")

        for name, obj in inspect.getmembers(py_dem_bones):
            if inspect.isfunction(obj) and obj.__module__.startswith('py_dem_bones'):
                rst.append(f".. py:function:: {name}{inspect.signature(obj)}")
                rst.append("")
                
                if obj.__doc__:
                    for line in obj.__doc__.split('\n'):
                        rst.append(f"   {line}")
                    rst.append("")

        return rst


class PyDemBonesExample(Directive):
    """Directive for including py-dem-bones examples."""
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'caption': directives.unchanged,
    }

    def run(self):
        env = self.state.document.settings.env
        example_path = self.arguments[0]
        
        # Check if the example is in docs/examples or examples directory
        docs_example_path = os.path.join(os.path.dirname(env.docname), example_path)
        main_example_path = os.path.join('..', 'examples', os.path.basename(example_path))
        
        # Try to find the example file
        if os.path.exists(os.path.join(env.app.srcdir, docs_example_path)):
            file_path = docs_example_path
        elif os.path.exists(os.path.join(env.app.srcdir, main_example_path)):
            file_path = main_example_path
        else:
            # If not found, show a more helpful error message
            return [self.state.document.reporter.warning(
                f'Example file {example_path} not found. Note that skeleton_example.py and animation_example.py ' 
                f'have been removed as they contained pseudocode for non-existent APIs.',
                line=self.lineno)]
        
        # Read the example file
        with open(os.path.join(env.app.srcdir, file_path), 'r') as f:
            code = f.read()
        
        # Create a literal block with the code
        literal = nodes.literal_block(code, code)
        literal['language'] = 'python'
        
        # Add caption if provided
        if 'caption' in self.options:
            caption = self.options['caption']
        else:
            caption = os.path.basename(example_path)
        
        container = nodes.container('', literal_block=True, classes=['literal-block-wrapper'])
        container.append(literal)
        
        # Add caption node
        caption_node = nodes.caption('', '', nodes.Text(caption))
        container.insert(0, caption_node)
        
        return [container]


def setup_html_theme(app: sphinx.application.Sphinx) -> None:
    """
    Set up custom HTML theme settings.
    """
    _LOG.info("[py-dem-bones] Setting up custom HTML theme")
    
    # Add custom CSS
    app.add_css_file('custom.css')
    
    # Add custom JavaScript
    app.add_js_file('custom.js')


def setup(app: sphinx.application.Sphinx) -> dict[str, bool | str]:
    """
    Set up the Sphinx extension.
    """
    app.setup_extension('sphinx.ext.autodoc')
    app.add_directive('py-dem-bones-api', PyDemBonesAPIDirective)
    app.add_directive('py-dem-bones-example', PyDemBonesExample)
    
    app.connect('builder-inited', setup_html_theme)
    
    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
