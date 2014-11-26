#!/c/Python27/python.exe
"""
Do './build_windows.py build' to build exe, then call
'makensis syncthing-gtk.nsis' to create instalation package.
"""

import os, site, sys, shutil, re
from cx_Freeze import setup, Executable
from cx_Freeze.freezer import Freezer, VersionInfo
from win32verstamp import stamp
from setup import get_version as _get_version

gnome_dll_path = "/Python27/Lib/site-packages/gnome"
build_dir = "./build/exe.win32-2.7/"

# List of dlls that cx_freeze can't detect automaticaly
missing_dll = [	'libgtk-3-0.dll',
				'libgdk-3-0.dll',
				'libatk-1.0-0.dll',
				'libcairo-gobject-2.dll',
				'libgdk_pixbuf-2.0-0.dll',
				'libgirepository-1.0-1.dll',
				'libgmodule-2.0-0.dll',
				'libgladeui-2-6.dll',
				'libpango-1.0-0.dll',
				'libpangocairo-1.0-0.dll',
				'libpangoft2-1.0-0.dll',
				'libpangowin32-1.0-0.dll',

				'libffi-6.dll',
				'libgio-2.0-0.dll',
				'libharfbuzz-gobject-0.dll',
				'libpng16-16.dll',
				'libxmlxpat.dll',
				'libgio-2.0-0.dll',
				'libintl-8.dll',
				'librsvg-2-2.dll',
				'libzzz.dll',
				'libffi-6.dll',
				'libjpeg-8.dll',
				'libwebp-4.dll',
				'libfreetype-6.dll',
				'libopenraw-7.dll',
				'libwinpthread-1.dll',
				
				'gspawn-win32-helper.exe',
				'gspawn-win32-helper-console.exe',
]

# List of dlls that are exported from wrong source (or broken for
# somehow other reason
wrong_sized_dll = [	'libcairo-gobject-2.dll',
					'libpangocairo-1.0-0.dll',
					'libfontconfig-1.dll',
					'libglib-2.0-0.dll',
					'libgobject-2.0-0.dll',
					'libgthread-2.0-0.dll',
]

include_files = []

# Stuff required by GTK
gtk_dirs = ('etc', 'lib')
include_files += [ (os.path.join(gnome_dll_path, x), x) for x in gtk_dirs ]
include_files += [ (os.path.join(gnome_dll_path, x), x) for x in missing_dll ]

# Data files
include_files += [ x for x in os.listdir(".") if x.endswith(".glade") ]
include_files += [ "./icons" ]

executables = [
	Executable(
		"scripts/syncthing-gtk-exe.py",
		compress = True,
		targetName = "syncthing-gtk.exe",
		base = "Win32GUI",
		icon = "icons/st-logo-128.ico",
	)
]


get_version = lambda : "%s-win32" % (_get_version(),)

# Monkey-patch _AddVersionResource in cx_Freeze so win32verstamp will
# not bitch about non-numeric version
RE_NUMBER = re.compile(r'v?([0-9]+).*')
extract_number = lambda x : RE_NUMBER.match(x).group(1) if \
		RE_NUMBER.match(x) else "0"
win32version = lambda x : ".".join([ extract_number(i) for i in x.split(".") ])
Freezer._AddVersionResource = lambda self, filename : \
	stamp(filename, VersionInfo(
			win32version(self.metadata.version),
			comments = self.metadata.long_description,
			description = self.metadata.description,
			company = self.metadata.author,
			product = self.metadata.name
	))

setup(
	name = "Syncthing GTK",
	author = "Kozec",
	version = get_version(),
	description = "Windows port of Sycnthing GTK",
	options = dict(
		build_exe = dict(
			compressed = False,
			includes = ["gi"],
			packages = ["gi"],
			include_files = include_files
		),
	),
	executables = executables
)

if 'build' in sys.argv:
	for l in wrong_sized_dll:
		print "replacing", l
		shutil.copy(
			os.path.join(gnome_dll_path, l),
			os.path.join(build_dir, l)
		)
	# Copy some theme icons
	sizes = ["16x16", "24x24", "32x32", "scalable"]
	icons = {	"status"  : [
					"image-missing",
					"dialog-information",
					"dialog-warning",
					"dialog-error",
					"checkbox-symbolic",
					"checkbox-mixed-symbolic",
					"checkbox-checked-symbolic",
				],
				"mimetypes" :	[ "text-html" ],
				"emblems" :		[ "emblem-system-symbolic" ],
				"apps" :		[ "utilities-terminal" ],
				"categories" :	[ "preferences-system" ],
				"places":		[ "user-home" ],
				"actions" : [
					"help-about",
					"edit-delete",
					"application-exit",
					"system-shutdown",
					"document-open",
					"view-refresh",
					"window-close-symbolic",
					"window-maximize-symbolic",
					"window-minimize-symbolic",
					"list-add-symbolic",
					"list-remove-symbolic",
					"pan-down-symbolic",
				],
				"devices" : [
					"drive-harddisk",
					"computer",
				],
		}
	themes = ["Adwaita"]
	target_path = os.path.join(build_dir, "share/icons/")
	src_path = os.path.join(gnome_dll_path, "share/icons/")
	for theme in themes:
		for size in sizes:
			extension = "svg" if size == "scalable" else "png"
			for cat in icons:
				try:
					os.makedirs(os.path.join(target_path, theme, size, cat))
				except Exception : pass
				for icon in icons[cat]:
					print "Copying icon %s/%s/%s/%s" % (theme, size, cat, icon)
					icon = "%s.%s" % (icon, extension)
					src = os.path.join(src_path, theme, size, cat, icon)
					dst = os.path.join(target_path, theme, size, cat, icon)
					if os.path.exists(src):
						shutil.copy(src, dst)
		print "Copying theme index for", theme
		shutil.copy(
			os.path.join(src_path, theme, "index.theme"),
			os.path.join(target_path, theme, "index.theme")
		)
	print "Copying glib schemas"
	if not os.path.exists(os.path.join(build_dir, "/share/glib-2.0/schemas")):
		target_path = os.path.join(build_dir, "share/glib-2.0/schemas")
		src_path = os.path.join(gnome_dll_path, "share/glib-2.0/schemas")
		if not os.path.exists(target_path):
			os.makedirs(target_path)
		for filename in os.listdir(src_path):
			src = os.path.join(src_path, filename)
			target = os.path.join(target_path, filename)
			shutil.copy(src, target)
	print "Storing version"
	file(os.path.join(build_dir, "__version__"), "w").write(get_version())
