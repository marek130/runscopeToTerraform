# runscopeToTerraform
Description: _python script to convert runscope buckets to terraform files._

**Requires: python3 interpreter.**

This script uses **requests**, **json** and **sys** library.

After running the script you will need to enter an **access_token** for runscope API. If you don't know where to get the access_token, check [this link](https://www.runscope.com/docs/api/authentication).

This script will create files in a directory where the script is located.

Parameters _webhooks_, _stop_on_failure_ and _emails_ are not supported in environments.
