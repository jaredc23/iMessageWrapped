# unmount existing mountpoint if present
diskutil unmount "/Volumes/iPhoneBackup" || true

# create sparsebundle (APFS). File will be at ~/iPhoneBackup.sparsebundle
hdiutil create -size 1t -type SPARSE -fs APFS -volname "iPhoneBackup" ~/iPhoneBackup.sparsebundle

# attach and mount at /Volumes/iPhoneBackup
hdiutil attach ~/iPhoneBackup.sparsebundle -mountpoint /Volumes/iPhoneBackup

# tighten permissions
chmod 700 /Volumes/iPhoneBackup