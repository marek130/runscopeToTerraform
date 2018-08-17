# runscopeToTerraform
Description: _python script to convert runscope buckets to terraform files._

**Requires: python3 interpreter.**

This script uses **requests**, **json**, **os** and **sys** library.

After running the script you will need to enter an **access_token** for runscope API and maximum number of tests which will be gotten from every bucket. If you don't know where to get the access_token, check [this link](https://www.runscope.com/docs/api/authentication).

This script will create folders with test files in a directory where the script is located.

Parameters _webhooks_, _stop_on_failure_ and _emails_ are not supported in environments.

# EXAMPLE #
If bucket called ```MyBucket``` has one test called ```Test``` with one test step, the output of the script will look like this:

File _MyBucket.tf_

```terraform
#create resource of type bucket
resource "runscope_bucket" "MyBucket" {
	name      = "MyBucket"
	team_uuid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
}

#create resource of type shared environment
resource "runscope_environment" "MyBucket_environment" {
	bucket_id         = "${runscope_bucket.MyBucket.id}"
	name              = "environment"
	regions           = ["eu1"]
	retry_on_failure  = false
	initial_variables = 
	  {
	    environment = "alpha",
	    apiVersion = "1.0",
	  },
	script            = "[]"
	verify_ssl        = true
	preserve_cookies  = false
	integrations      = []
	remote_agents     = []
}

module "tests_MyBucket" {
	source    = "./MyBucket_TESTS"

	bucket_id = "${runscope_bucket.MyBucket.id}"
}
```

Folder _MyBucket_TESTS_ will look like this:

```
➜  MyBucket_TESTS tree
.
|-- Test.tf
`-- variables.tf
```

File _Test.tf_ looks like this:

```terafform
resource "runscope_test" "Test" {
	name        = "Test"
	description = ""
	bucket_id   = "${var.bucket_id}"
}

resource "runscope_step" "step0_Test" {
	bucket_id      = "${var.bucket_id}"
	test_id        = "${runscope_test.Test.id}"
	step_type      = "request"
	url            = "https://{{environment}}example.com/{{apiVersion}}"
	method         = "GET"
	headers		   = {
		header   = "x-api-key"
		value    = "adasdadlakdadlkajdakdjalksjdsadlakdsjk"
	}
	assertions     = [
	  {
	    comparison = "equal_number",
	    value = "200",
	    source = "response_status",
	  },
	]
	variables      = [
	]
	scripts        = ["var data = JSON.parse(response.body);\n"]
	before_scripts = []
	body           = ""
}

resource "runscope_schedule" "schedule0_Test" {
		bucket_id      = "${var.bucket_id}"
		test_id        = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
		interval       = "6h"
		environment_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
		note           = ""
}
```
