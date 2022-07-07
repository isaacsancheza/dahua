from distutils.core import setup

package = {
      'name': 'dahua',
      'version': '1.0',
      'description': 'Python Wrapper for Dahua IPC HTTP API v2.76',

      'author': 'Isaac Sánchez',
      'license': 'MIT',

      'requires': [
            'requests==2.28.1',
      ],

      'packages': [
            'dahua',
      ],

}

setup(**package)
