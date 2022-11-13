# xbvr-matcher
This script helps match files in xbvr based on file hashes in stasshdb.org.

Stashdb.org is a crowd sourced metadatabase for porn and contains file hashes along with metadata.
This script connects to xbvr and looks up the file hashes to see if there is a match and uses this to help match files to existing metadata in xbvr.

stashdb.org is still under development and currently requires an invite code to register an account.
To get an invite join the stash discord https://discord.gg/2TsNFKt and go to the #stashdb-invites channel and find an invite code pinned to the channel.
Once registered login and generate an api key.

The script uses environment variables for configuration.
* **XBVR_HOST** - url of xbvr instance
* **STASHDB_ENDPOINT** - endpoint of stashbox, default https://stashdb.org/graphql
* **STASHDB_KEY** - api key for your stashdb account

Running:

```python xbvr-matcher.py```