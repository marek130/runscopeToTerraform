import json

def createEnvironment(test, bucket):
	jsonData = test.testDetail 
	for index, environment in enumerate(jsonData["environments"]):
		bucket.allEnvironments[environment["id"]] = "runscope_environment." + str(index) + editName(bucket.jsonData["name"]) + "_" + editName(jsonData["name"]) + "_" + editName(environment["name"]) + ".id"
		test.dataToFile += """resource "runscope_environment" "{}{}_{}_{}" {{
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
	{}
}}\n\n""".format(index, editName(bucket.jsonData["name"]), editName(jsonData["name"]), editName(environment["name"]), editName(jsonData["name"]), environment["name"], json.dumps(environment["regions"]), str(environment["retry_on_failure"]).lower(), (editAssertions(environment["initial_variables"]) if environment["initial_variables"] != None else "{}") if environment["parent_environment_id"] == None else editAssertions(getIntialValues(environment["parent_environment_id"], bucket.sharedEnvironments)), json.dumps(environment["script"]) if environment["script"] != None else "\"\"", str(environment["verify_ssl"]).lower(), str(environment["preserve_cookies"]).lower(), json.dumps(getIntegrations(environment["integrations"])), editAssertions(environment["remote_agents"]) if len(environment["remote_agents"]) > 0 else [], extension(environment) if bucket.extension else "")


def createSharedEnvironment(bucket):
	for environment in bucket.sharedEnvironments:
		bucket.allEnvironments[environment["id"]] = "var.shared_environment_" + editName(bucket.jsonData["name"]) + "_" + editName(environment["name"])
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
  	{}
}}\n\n""".format(editName(bucket.jsonData["name"]), editName(environment["name"]), editName(bucket.jsonData["name"]), environment["name"], json.dumps(environment["regions"]), str(environment["retry_on_failure"]).lower(), editAssertions(environment["initial_variables"]) if environment["initial_variables"] != None else "{}", json.dumps(environment["script"]) if environment["script"] != None else "\"\"", str(environment["verify_ssl"]).lower(), str(environment["preserve_cookies"]).lower(), json.dumps(getIntegrations(environment["integrations"])), editAssertions(environment["remote_agents"]) if len(environment["remote_agents"]) > 0 else [], extension(environment) if bucket.extension else "")



def createSchedule(test, bucket):
	jsonData = test.testDetail
	for index, schedule in enumerate(jsonData["schedules"]):
		test.dataToFile += """resource \"runscope_schedule\" \"schedule{}_{}\" {{
	bucket_id      = \"${{var.bucket_id}}\"
	test_id        = \"${{runscope_test.{}.id}}\"
	interval       = \"{}\"
	environment_id = \"${{{}}}\"
	note           = \"{}\"
}}\n\n""".format(index, editName(jsonData["name"]), editName(jsonData["name"]), schedule["interval"], bucket.allEnvironments[schedule["environment_id"]], schedule["note"] if schedule["note"] != None else "")


def createTestStep(test, bucket):
	jsonData = test.testDetail
	for index, step in enumerate(jsonData["steps"]):
		if step['step_type'] == 'pause':
			print('\n Atention: Pause step skipped ({} / {})'.format(test.jsonData['name'], bucket.jsonData['name']))
			continue
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
	{}
}}\n\n""".format(index, editName(jsonData["name"]), editName(jsonData["name"]), step["step_type"], step["url"], step["method"], getHeaders(jsonData, step["headers"], bucket), editAssertions(step["assertions"]), editAssertions(step["variables"]), json.dumps(step["scripts"]) if "scripts" in step and step["scripts"] != [''] else [], json.dumps(step["before_scripts"]) if "before_scripts" in step else [], json.dumps(step["body"]) if "body" in step and step["body"] != None else "\"\"", dependsOn(index, jsonData["name"]))


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
	source         = \"./{}\"

	bucket_id      = \"${{runscope_bucket.{}.id}}\"
	{}
}}""".format(editName(bucket.jsonData["name"]), folder, editName(bucket.jsonData["name"]), getSharedEnv(bucket))


def getSharedEnv(bucket):
	result = ""
	for env in bucket.sharedEnvironments:
		result += "shared_environment_" + editName(bucket.jsonData["name"]) + "_" + editName(env["name"]) + " = \"${runscope_environment.shared_environment_" + editName(bucket.jsonData["name"]) + "_" + editName(env["name"]) + ".id}\"\n"
	return result



def makeMainFile(access_token):
	print("\nCreating init file")
	f = open("main.tf", "w")
	f.write("""provider "runscope" {
  access_token = "%s"
}""" % (access_token))
	f.close()


def getIntegrations(jsonData):
	result = []
	for i in jsonData:
		result.append(i["id"])
	return result

def createVariables(folderName, bucket):
	f = open(folderName + "/variables.tf", "w")
	sharedEnvironments = ""
	for env in bucket.sharedEnvironments:
		sharedEnvironments += """variable "{}" {{}}\n""".format("shared_environment_" + editName(bucket.jsonData["name"]) + "_" + editName(env["name"]))
	f.write("""variable "bucket_id" {{}}\n{}""".format(sharedEnvironments))
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

def dependsOn(index, stepName):
	if index != 0:
		return """depends_on     = ["{}{}_{}"]""".format("runscope_step.step", index -1, editName(stepName))
	else:
		return ""

def getIntialValues(envID, sharedEnvironments):
	for sharedEnv in sharedEnvironments:
		if envID == sharedEnv["id"]:
			return sharedEnv["initial_variables"]

def editEnvironments(bucket):
	bucket.editedEnvironments = True
	for environment in bucket.sharedEnvironments:
		if environment["headers"] != None:
			for key in environment["headers"]:
				environment["headers"][key] = environment["headers"][key].pop() # we get array with value ['value'], but we just want a single value

def extension(environment):
	return """
	webhooks                = {}
    emails                  = 
      {{
      	notify_all       = {}
      	notify_on        = \"{}\"
      	notify_threshold = {}

      	recipients       = [{}
      	]

      }}""".format(json.dumps(environment["webhooks"]) if environment["webhooks"] != None else [], str(environment["emails"]["notify_all"]).lower(), environment["emails"]["notify_on"] if environment["emails"]["notify_on"] != None else "", environment["emails"]["notify_threshold"], editAssertions(environment["emails"]["recipients"]))


def useSharedEnv(jsonData, sharedEnvironments):
	for schedule in jsonData["schedules"]:
		envID = schedule["environment_id"]
		for sharedEnv in sharedEnvironments:
			if envID == sharedEnv["id"]:
				return True
			for env in jsonData["environments"]:
				if env["parent_environment_id"] == sharedEnv["id"]:
					return True
	return False


def getHeaders(jsonData, headers, bucket):
	result = {}
	if useSharedEnv(jsonData, bucket.sharedEnvironments):
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

