import json

def createEnvironment(test, bucketName):
	jsonData = test.testDetail
	for environment in jsonData["environments"]:
		test.dataToFile += """resource "runscope_environment" "{}_{}_{}" {{
	bucket_id         = \"${{var.bucket_id}}\"
	test_id           = \"${{runscope_test.{}.id}}\"
	name              = \"{}\"
	regions           = {}
	retry_on_failure  = {}
	initial_variables = {}
	script            = {}
	verify_ssl        = {}
	preserve_cookies  = {}
	integrations      = {}
	remote_agents     = {}
}}\n\n""".format(editName(bucketName), editName(jsonData["name"]), editName(environment["name"]), editName(jsonData["name"]), environment["name"], json.dumps(environment["regions"]), str(environment["retry_on_failure"]).lower(), editAssertions(environment["initial_variables"]) if environment["initial_variables"] != None else "{}", json.dumps(environment["script"]) if environment["script"] != None else "\"\"", str(environment["verify_ssl"]).lower(), str(environment["preserve_cookies"]).lower(), json.dumps(getIntegrations(environment["integrations"])), environment["remote_agents"])



def createSharedEnvironment(bucket):
	# parameters webhooks, stop_on_failure, emails and headers are not supported
	for environment in bucket.sharedEnvironments:
		bucket.dataToFile += """resource \"runscope_environment\" \"shared_environment_{}_{}\" {{
	bucket_id         = \"${{runscope_bucket.{}.id}}\"
	name              = \"{}\"
	regions           = {}
	retry_on_failure  = {}
	initial_variables = {}
	script            = {}
	verify_ssl        = {}
	preserve_cookies  = {}
	integrations      = {}
	remote_agents     = {}
}}\n\n""".format(editName(bucket.jsonData["name"]), editName(environment["name"]), editName(bucket.jsonData["name"]), environment["name"], json.dumps(environment["regions"]), str(environment["retry_on_failure"]).lower(), editAssertions(environment["initial_variables"]) if environment["initial_variables"] != None else "{}", json.dumps(environment["script"]) if environment["script"] != None else "\"\"", str(environment["verify_ssl"]).lower(), str(environment["preserve_cookies"]).lower(), json.dumps(getIntegrations(environment["integrations"])), environment["remote_agents"])


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
	print("\n\033[92mOk\033[0m")

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


def getHeaders(headers, bucket):
	result = {}
	for index in range(len(bucket.sharedEnvironments)):
		if bucket.sharedEnvironments[index]["headers"] != None:
			for key in bucket.sharedEnvironments[index]["headers"]:
				bucket.sharedEnvironments[index]["headers"][key] = bucket.sharedEnvironments[index]["headers"][key].pop()
			result.update(bucket.sharedEnvironments[index]["headers"])
	if headers != None:
		for key in headers:
			headers[key] = headers[key].pop()
		result.update(headers)
	resultText = "headers\t\t   = {"
	for key in result:
		resultText += """
		header   = \"{}\"
		value    = \"{}\"\n""".format(key, result[key])
	resultText += "\t}"
	return "" if not result else resultText

