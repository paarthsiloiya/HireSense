



import os
import sys
sys.path.insert(0, os.path.abspath('../..'))




project = 'HireSense'
copyright = '2024-2026, HireSense Team'
author = 'HireSense Team'
release = '1.0'
version = '1.0.0'




extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']




html_theme = 'shibuya'
html_static_path = ['_static']


html_theme_options = {
    "accent_color": "green",
    "dark_code": True,
    "github_url": "https://github.com/paarthsiloiya/HireSense",
    "nav_links": [
        {
            "title": "Guides",
            "url": "https://github.com/paarthsiloiya/HireSense/tree/main/docs/guides",
        },
        {
            "title": "Contributing",
            "url": "https://github.com/paarthsiloiya/HireSense/blob/main/CONTRIBUTING.md",
        },
    ],
}


html_context = {
    "source_type": "github",
    "source_user": "paarthsiloiya",
    "source_repo": "HireSense",
}


autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}


napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None


intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'flask': ('https://flask.palletsprojects.com/en/3.0.x/', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/20/', None),
}


autosummary_generate = True
