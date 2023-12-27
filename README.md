# Command FS

A fuse filesystem that proxies all requests to a given directory, but pipes the contents of a file through a command on read.
This is useful, for example, for transparently decrypting files.

## Usage

Create a source directory (e.g. `src`).
Createa mountpoint (e.g. `dst`).

A proof of concept example, that fully proxies files
```
python command_fs.py src dst cat
```

An example to base64 encode files
```
python command_fs.py src dst base64
```

An example to decrypt all files with gpg
```
python command_fs.py src dst "gpg --decrypt"
```

An example to inject all files with 1password
```
python command_fs.py src dst "op inject -i /dev/stdin"
```
