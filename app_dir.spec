# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# 获取项目路径
project_path = os.path.abspath('.')
word_learner_path = os.path.join(project_path, 'word_learner')

a = Analysis(
    ['word_learner/launcher.py'],
    pathex=[word_learner_path, project_path],
    binaries=[],
    datas=[
        ('word_learner/app.py', '.'),
        ('word_learner/api_service.py', '.'),
        ('word_learner/camera.py', '.'),
        ('word_learner/review.py', '.'),
        ('word_learner/words.py', '.'),
        ('word_learner/album.py', '.'),
        ('word_learner/utils.py', '.'),
        ('word_learner/word_details.py', '.'),
        ('word_learner/image_manager.py', '.'),
        ('word_learner/TtsPlayer.py', '.'),
        ('word_learner/settings.py', '.'),
        ('word_learner/images', 'images'),
        ('word_learner/words.db', '.'),
        ('word_learner/settings.json', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._tkinter_finder',
        'requests',
        'sqlite3',
        'json',
        'threading',
        'time',
        're',
        'subprocess',
        'webbrowser',
        'datetime',
        'base64',
        'io',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tensorflow',
        'torch',
        'cv2',
        'pygame',
        'jupyter',
        'IPython',
        'notebook',
        'qtpy',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'kivy',
        'django',
        'flask',
        'fastapi',
        'unittest',
        'test',
        'tests',
        'distutils',
        'setuptools',
        'pip',
        'wheel',
        'doctest',
        'pydoc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # 关键：这里设置为True使用目录模式
    name='WordLearnerApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,  # 关闭UPX压缩以提高启动速度
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT用于目录模式打包
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=False,
    upx_exclude=[],
    name='WordLearnerApp'  # 这将创建一个包含所有文件的目录
)

# BUNDLE创建.app包
app = BUNDLE(
    coll,  # 注意这里使用coll而不是exe
    name='WordLearnerApp.app',
    bundle_identifier='com.yourname.wordlearner',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDisplayName': 'Word Learner',
        'CFBundleGetInfoString': "Word Learning Application",
        'CFBundleIdentifier': "com.yourname.wordlearner",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': "Copyright © 2024 Your Name. All rights reserved.",
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
    },
)