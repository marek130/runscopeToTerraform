import requests
import sys
import os
import terraform

class RunscopeAPI(object):

	def __init__(self, access_token, count):
		self.access_token = access_token
		self.count        = count

	def checkReturnedCode(self, jsonData):
		if jsonData["error"] != None:
			print("\n\033[91mResponse code: %s\nMessage: %s\033[0m" % (jsonData["error"]["status"] if "status" in jsonData["error"] else jsonData["meta"]["status"], jsonData["error"]["message"]))

	def getAllBuckets(self, extension):
		r = requests.get("https://api.runscope.com/buckets", headers={"Authorization":"Bearer %s" % (self.access_token)})
		self.checkReturnedCode(r.json())
		return [Bucket(jsonData, extension) for jsonData in r.json()["data"]]

	def getTestsFromBucket(self, bucket):
		link = "https://api.runscope.com/buckets/" + bucket.jsonData["key"] + "/tests?count=" + self.count
		r = requests.get(link, headers={"Authorization":"Bearer %s" % (self.access_token)})
		self.checkReturnedCode(r.json())
		bucket.tests = [Test(jsonData) for jsonData in r.json()["data"]]

	def getTestDetail(self, bucket, test):
		link = "https://api.runscope.com/buckets/" + bucket.jsonData["key"] + "/tests/" + test.jsonData["id"]
		r = requests.get(link, headers={"Authorization":"Bearer %s" % (self.access_token)})
		self.checkReturnedCode(r.json())
		test.testDetail = r.json()["data"]

	def getSharedEnvironments(self, bucket):
		link = "https://api.runscope.com/buckets/" + bucket.jsonData["key"] + "/environments"
		r = requests.get(link, headers={"Authorization":"Bearer %s" % (self.access_token)})
		self.checkReturnedCode(r.json())
		bucket.sharedEnvironments = r.json()["data"] # list of shared environments


class Bucket(object):

	def __init__(self, jsonData, extension):
		self.jsonData           = jsonData
		self.tests              = []
		self.sharedEnvironments = []
		self.allEnvironments    = {}
		self.dataToFile         = "" # data which will be written into a file
		self.editedEnvironments = False
		self.extension          = extension # if parameters webhooks and emails will be included


class Test(object):

	def __init__(self, jsonData):
		self.jsonData   = jsonData
		self.testDetail = {}
		self.dataToFile = "" # data which will be written into a file

def createNewFile(textToFile, fileName):
	f = open(terraform.editName(fileName) + ".tf", "w")
	f.write(textToFile)
	f.close()


def createFileTest(textToFile, folderName, fileName):
	f = open(folderName + "/" + terraform.editName(fileName) + ".tf", "w")
	f.write(textToFile)
	f.close()

def createFolder(folderName):
	newName = terraform.editName(folderName) + "_TESTS"
	if not os.path.exists(newName):
		os.makedirs(newName)
	return newName


def initprogressBar(length):
	sys.stdout.write("\nWill creat %d folders with test files\n..." % (length))
	sys.stdout.flush()

def progressBarStep(length, testName, index):
	sys.stdout.write("\033[K") #clear line
	text = "#%s \033[95mCreated '%s.tf' file.\033[0m %s%%" % ("_" * (length - (index+1)), terraform.editName(testName), str(100*(index+1)/length))
	sys.stdout.write(text)
	sys.stdout.flush()
	sys.stdout.write("\b" * (len(text) - 10))
	sys.stdout.flush()


def parse(access_token, numberOfTests, extension):
	api = RunscopeAPI(access_token, numberOfTests)
	buckets = api.getAllBuckets(extension)
	initprogressBar(len(buckets))
	i = 1
	for bucket in buckets:
		folderName = createFolder(bucket.jsonData["name"])
		terraform.createBucket(bucket)
		api.getTestsFromBucket(bucket)
		api.getSharedEnvironments(bucket)
		terraform.createSharedEnvironment(bucket)
		terraform.createVariables(folderName,  bucket)
		print("\n%d) Create folder %s and %d test files:" % (i, terraform.editName(bucket.jsonData["name"]), len(bucket.tests)))
		for index, test in enumerate(bucket.tests):
			terraform.createTest(test)
			api.getTestDetail(bucket, test)
			terraform.createTestStep(test, bucket)
			terraform.createEnvironment(test, bucket)
			terraform.createSchedule(test, bucket)
			createFileTest(test.dataToFile, folderName, test.jsonData["name"])
			progressBarStep(len(bucket.tests), test.jsonData["name"], index)
		terraform.createModule(bucket, folderName)
		createNewFile(bucket.dataToFile, bucket.jsonData["name"])
		i += 1
	print("\n\033[92mCompleted!\033[0m")

def main():
	access_token  = input("Enter an access_token for runscope: ")
	numberOfTests = input("How many tests you would like to get from every bucket: ")
	extension     = input("Do you want to use webhooks and emails?[y/n] ")
	extension = extension == "y"
	terraform.makeMainFile(access_token)
	parse(access_token, numberOfTests, extension)

main()
