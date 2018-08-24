import json

def createEnvironment(test, bucketName):
	# parameters webhooks, stop_on_failure, emails and headers are not supported
	jsonData = test.testDetail
	for environment in jsonData["environments"]:
		test.dataToFile += """resource "runscope_environment" "{}_{}_{}" {{
	bucket_id               = \"${{var.bucket_id}}\"
	test_id                 = \"${{runscope_test.{}.id}}\"
	name                    = \"{}\"
	regions                 = {}
	retry_on_failure        = {}
	initial_variables       = {}
	script                  = {}
	verify_ssl              = {}
	preserve_cookies        = {}
	integrations            = {}
	remote_agents           = {}
    webhooks                = {}
    emails                  = 
      {{
      	notify_all       = {}
      	notify_on        = \"{}\"
      	notify_threshold = {}

      	recipients       = [{}
      	]

      }}
}}\n\n""".format(editName(bucketName), editName(jsonData["name"]), editName(environment["name"]), editName(jsonData["name"]), environment["name"], json.dumps(environment["regions"]), str(environment["retry_on_failure"]).lower(), editAssertions(environment["initial_variables"]) if environment["initial_variables"] != None else "{}", json.dumps(environment["script"]) if environment["script"] != None else "\"\"", str(environment["verify_ssl"]).lower(), str(environment["preserve_cookies"]).lower(), json.dumps(getIntegrations(environment["integrations"])), editAssertions(environment["remote_agents"]) if len(environment["remote_agents"]) > 0 else [], json.dumps(environment["webhooks"]) if environment["webhooks"] != None else [], str(environment["emails"]["notify_all"]).lower(), environment["emails"]["notify_on"] if environment["emails"]["notify_on"] != None else "", environment["emails"]["notify_threshold"], editAssertions(environment["emails"]["recipients"]))


def createSharedEnvironment(bucket):
	# parameters webhooks, stop_on_failure, emails and headers are not supported
	for environment in bucket.sharedEnvironments:
		bucket.dataToFile += """resource \"runscope_environment\" \"shared_environment_{}_{}\" {{
	bucket_id               = \"${{runscope_bucket.{}.id}}\"
	name                    = \"{}\"
	regions                 = {}
	retry_on_failure        = {}
	initial_variables       = {}
	script                  = {}
	verify_ssl              = {}
	preserve_cookies        = {}
	integrations            = {}
	remote_agents           = {}
    webhooks                = {}
    emails                  = 
      {{
      	notify_all       = {}
      	notify_on        = \"{}\"
      	notify_threshold = {}

      	recipients       = [{}
      	]

      }}
}}\n\n""".format(editName(bucket.jsonData["name"]), editName(environment["name"]), editName(bucket.jsonData["name"]), environment["name"], json.dumps(environment["regions"]), str(environment["retry_on_failure"]).lower(), editAssertions(environment["initial_variables"]) if environment["initial_variables"] != None else "{}", json.dumps(environment["script"]) if environment["script"] != None else "\"\"", str(environment["verify_ssl"]).lower(), str(environment["preserve_cookies"]).lower(), json.dumps(getIntegrations(environment["integrations"])), editAssertions(environment["remote_agents"]) if len(environment["remote_agents"]) > 0 else [], json.dumps(environment["webhooks"]) if environment["webhooks"] != None else [], str(environment["emails"]["notify_all"]).lower(), environment["emails"]["notify_on"] if environment["emails"]["notify_on"] != None else "", environment["emails"]["notify_threshold"], editAssertions(environment["emails"]["recipients"]))


def createSchedule(test):
	jsonData = test.testDetail
	for index, schedule in enumerate(jsonData["schedules"]):
		test.dataToFile += """resource \"runscope_schedule\" \"schedule{}_{}\" {{
	bucket_id      = \"${{var.bucket_id}}\"
	test_id        = \"{}\"
	interval       = \"{}\"
	environment_id = \"{}\"
	note           = \"{}\"
}}\n\n""".format(index, editName(jsonData["name"]), jsonData["id"], schedule["interval"], schedule["environment_id"], schedule["note"] if schedule["note"] != None else "")


def createTestStep(test, bucket):
	jsonData = test.testDetail
	for index, step in enumerate(jsonData["steps"]):
		test.dataToFile += """resource \"runscope_step\" \"step{}_{}\" {{
	bucket_id      = \"${{var.bucket_id}}\"
	test_id        = \"${{runscope_test.{}.id}}\"
	step_type      = \"{}\"
	url            = \"{}\"
	method         = \"{}\"
	{}
	assertions     = [{}
	]
	variables      = [{}
	]
	scripts        = {}
	before_scripts = {}
	body           = {}
}}\n\n""".format(index, editName(jsonData["name"]), editName(jsonData["name"]), step["step_type"], step["url"], step["method"], getHeaders(step["headers"], bucket), editAssertions(step["assertions"]), editAssertions(step["variables"]), json.dumps(step["scripts"]) if "scripts" in step and step["scripts"] != [''] else [], json.dumps(step["before_scripts"]) if "before_scripts" in step else [], json.dumps(step["body"]) if "body" in step else "\"\"")


def createTest(test):
	jsonData = test.jsonData
	test.dataToFile += """resource \"runscope_test\" \"{}\" {{
	name        = \"{}\"
	description = {}
	bucket_id   = \"${{var.bucket_id}}\"
}}\n\n""".format(editName(jsonData["name"]), jsonData["name"], json.dumps(jsonData["description"]) if jsonData["description"] != None else "\"\"")


def createBucket(bucket):
	bucket.dataToFile += """resource \"runscope_bucket\" \"{}\" {{
	name      = \"{}\"
	team_uuid = \"{}\"
}}\n\n""".format(editName(bucket.jsonData["name"]), bucket.jsonData["name"], bucket.jsonData["team"]["id"])

def createModule(bucket, folder):
	bucket.dataToFile += """module \"tests_{}\" {{
	source    = \"./{}\"

	bucket_id = \"${{runscope_bucket.{}.id}}\"
}}""".format(editName(bucket.jsonData["name"]), folder, editName(bucket.jsonData["name"]))

def makeInitFile(access_token):
	print("\nCreating init file")
	f = open("init.tf", "w")
	f.write("""terraform {
  required_version = ">= 0.10.0"
}
provider "runscope" {
  access_token = "%s"
}""" % (access_token))
	f.close()

def createVariables(folderName):
	f = open(folderName + "/variables.tf", "w")
	f.write("""variable "bucket_id" {}""")
	f.close()

def editAssertions(jsonText):
	if type(jsonText) != list:
		jsonText = [jsonText]
	result = ""
	for i in jsonText:
		result += "\n\t  {\n"
		for j in i.keys():
			result += "\t    {} = \"{}\",\n".format(j, "" if i[j] == "\"\"" else i[j])
		result += "\t  },"
	return result

def editName(fileName):
	result = ""
	for char in fileName:
		if char in " /?":
			result += "_"
		elif not char.isalnum():
			continue
		else:
			result += char
	return result

def getIntegrations(jsonData):
	result = []
	for i in jsonData:
		result.append(i["id"])
	return result


def editEnvironments(bucket):
	bucket.editedEnvironments = True
	for environment in bucket.sharedEnvironments:
		if environment["headers"] != None:
			for key in environment["headers"]:
				environment["headers"][key] = environment["headers"][key].pop() # we get array with value ['value'], but we just want a single value

def getHeaders(headers, bucket):
	result = {}
	if not bucket.editedEnvironments:
		editEnvironments(bucket)
	for env in bucket.sharedEnvironments: 
		if env["headers"] != None: result.update(env["headers"])

	if headers != None:
		for key in headers:
			headers[key] = headers[key].pop() # we get array with value ['value'], but we just want a single value
		result.update(headers)
	resultText = "headers\t\t   = {"
	for key in result:
		resultText += """
		header   = \"{}\"
		value    = \"{}\"\n""".format(key, result[key])
	resultText += "\t}"
	return "" if not result else resultText

