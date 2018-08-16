import requests
import json
import sys

def getAllBuckets(header):
	r = requests.get("https://api.runscope.com/buckets", headers={"Authorization":"Bearer %s" % (header)})
	if r.status_code != 200:
		print("\n\033[91mSomething went wrong in request on buckets.\nResponse code: ", r.status_code, "\033[0m")
	return r.json()["data"] # list of bucket in JSON format

def getTestsFromBucket(bucketKey, header):
	link = "https://api.runscope.com/buckets/" + bucketKey + "/tests"
	r = requests.get(link, headers={"Authorization":"Bearer %s" % (header)})
	if r.status_code != 200:
		print("\n\033[91mSomething went wrong in request on tests from bucket.\nResponse code: ", r.status_code, "\033[0m")
	return r.json()["data"] # list of tests from the given bucket in JSON format

def getTestDetail(bucketKey, testID, header):
	link = "https://api.runscope.com/buckets/" + bucketKey + "/tests/" + testID
	r = requests.get(link, headers={"Authorization":"Bearer %s" % (header)})
	if r.status_code != 200:
		print("\n\033[91mSomething went wrong in request on test's detail.\nResponse code: ", r.status_code, "\033[0m")
	return r.json()["data"]

def getSharedEnviroments(bucketKey, header):
	link = "https://api.runscope.com/buckets/" + bucketKey + "/environments"
	r = requests.get(link, headers={"Authorization":"Bearer %s" % (header)})
	if r.status_code != 200:
		print("\n\033[91mSomething went wrong in shared environment request.\nResponse code: ", r.status_code, "\033[0m")
	return r.json()["data"] # list of shared environments

def createNewFile(textToFile, fileName):
	f = open(fileName + ".tf", "w")
	f.write(textToFile)
	f.close()

def getIntegrations(jsonData):
	result = []
	for i in jsonData:
		result.append(i["id"])
	return result

def createEnvironment(jsonData, bucketName):
	# parameters webhooks, stop_on_failure, emails and headers are not supported
	result = ""
	for index,_ in enumerate(jsonData):
		result += """resource \"runscope_environment\" \"{}_{}\" {{
	bucket_id         = \"${{runscope_bucket.{}.id}}\"
	name              = \"{}\"
	regions           = {}
	retry_on_failure  = {}
	initial_variables = {}
	script            = \"{}\"
	verify_ssl        = {}
	preserve_cookies  = {}
	integrations      = {}
	remote_agents     = {}
}}\n\n""".format(editName(bucketName), editName(jsonData[index]["name"]), editName(bucketName), jsonData[index]["name"], json.dumps(jsonData[index]["regions"]), str(jsonData[index]["retry_on_failure"]).lower(), editAssertions(jsonData[index]["initial_variables"]) if jsonData[index]["initial_variables"] != None else "{}", jsonData[index]["script"] if jsonData[index]["script"] != None else [], str(jsonData[index]["verify_ssl"]).lower(), str(jsonData[index]["preserve_cookies"]).lower(), json.dumps(getIntegrations(jsonData[index]["integrations"])), jsonData[index]["remote_agents"])
	return result

def createSchedule(jsonData, bucket):
	result = ""

	for index, _ in enumerate(jsonData["schedules"]):
		result += """resource \"runscope_schedule\" \"schedule{}_{}\" {{
		bucket_id      = \"${{runscope_bucket.{}.id}}\"
		test_id        = \"{}\"
		interval       = \"{}\"
		environment_id = \"{}\"
		note           = \"{}\"
}}\n\n""".format(index, editName(jsonData["name"]), editName(bucket["name"]), jsonData["id"], jsonData["schedules"][index]["interval"], jsonData["schedules"][index]["environment_id"], jsonData["schedules"][index]["note"] if jsonData["schedules"][index]["note"] != None else "")

	return result

def createTestStep(jsonData, bucket, access_token):
	result = ""


	for index, _ in enumerate(jsonData["steps"]):
		result += """resource \"runscope_step\" \"step{}_{}\" {{
	bucket_id      = \"${{runscope_bucket.{}.id}}\"
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
}}\n\n""".format(index, editName(jsonData["name"]), editName(bucket["name"]), editName(jsonData["name"]), jsonData["steps"][index]["step_type"], jsonData["steps"][index]["url"], jsonData["steps"][index]["method"], getHeaders(jsonData["steps"][index]["headers"], jsonData["id"], bucket["key"], access_token), editAssertions(jsonData["steps"][index]["assertions"]), editAssertions(jsonData["steps"][index]["variables"]), json.dumps(jsonData["steps"][index]["scripts"]) if "scripts" in jsonData["steps"][index] and jsonData["steps"][index]["scripts"] != [''] else [], json.dumps(jsonData["steps"][index]["before_scripts"]) if "before_scripts" in jsonData["steps"][index] else [], json.dumps(jsonData["steps"][index]["body"]) if "body" in jsonData["steps"][index] else "\"\"")
	return result


def createTest(jsonData, bucketName):
	return """resource \"runscope_test\" \"{}\" {{
	name        = \"{}\"
	description = {}
	bucket_id   = \"${{runscope_bucket.{}.id}}\"
}}\n\n""".format(editName(jsonData["name"]), editName(jsonData["name"]), json.dumps(jsonData["description"]) if jsonData["description"] != None else "\"\"", editName(bucketName))


def createBucket(jsonData):
	return """resource \"runscope_bucket\" \"{}\" {{
	  name      = \"{}\"
	  team_uuid = \"{}\"
}}\n\n""".format(editName(jsonData["name"]), jsonData["name"], jsonData["team"]["id"])

def getHeaders(headers, testID, bucketKey, access_token):
	result = {}
	headersFromEnviroment = getSharedEnviroments(bucketKey, access_token)
	for index in range(len(headersFromEnviroment)):
		if headersFromEnviroment[index]["headers"] != None:
			for key in headersFromEnviroment[index]["headers"]:
				headersFromEnviroment[index]["headers"][key] = headersFromEnviroment[index]["headers"][key].pop()
			result.update(headersFromEnviroment[index]["headers"])
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

def initprogressBar(length):
	sys.stdout.write("\n")
	# setup toolbar
	sys.stdout.write("Creating %d terraform files\n..." % (length))
	sys.stdout.flush()
	sys.stdout.write("\b" * (length))

def progressBarStep(length, bucketName, index):
	sys.stdout.write("#%s \033[95mCreating '%s.tf' file.\033[0m %s%%           " % ("_" * (length - (index+1)), bucketName, str(100*(index+1)/length)))
	sys.stdout.flush()
	sys.stdout.write("\b" * (len(bucketName) + 33 + (length - index) + len(str(100*(index+1)/length))))
	sys.stdout.flush()



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

def parse(access_token):
	buckets = getAllBuckets(access_token)
	initprogressBar(len(buckets))
	i = 0
	for bucket in buckets:
		result = ""
		result += createBucket(bucket)
		testsInBucket = getTestsFromBucket(bucket["key"], access_token)
		for test in testsInBucket:
			result += createTest(test, bucket["name"])
			testDetail = getTestDetail(bucket["key"], test["id"], access_token)
			result += createTestStep(testDetail, bucket, access_token)
			result += createSchedule(testDetail, bucket)
		enviroments = getSharedEnviroments(bucket["key"], access_token)
		result += createEnvironment(enviroments, bucket["name"])
		createNewFile(result, bucket["name"])
		progressBarStep(len(buckets), bucket["name"], i)
		i += 1
	print("\n\033[92mCompleted!\033[0m")

def main():
	access_token = input("Enter an access_token for runscope: ")
	makeInitFile(access_token)
	parse(access_token)

main()