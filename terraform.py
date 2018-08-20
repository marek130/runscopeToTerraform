import requests
import sys
import os
import runscope

class RunscopeAPI(object):
	"""docstring for RunscopeAPI"""
	def __init__(self, access_token, count):
		self.access_token = access_token
		self.count        = count

	def checkReturnedCode(self, jsonData):
		if jsonData["meta"]["status"] != "success":
			print("\n\033[91mResponse code: %s\nMessage: %s\033[0m" % (jsonData["error"]["status"], jsonData["error"]["message"]))

	def getAllBuckets(self):
		r = requests.get("https://api.runscope.com/buckets", headers={"Authorization":"Bearer %s" % (self.access_token)})
		self.checkReturnedCode(r.json())
		return [Bucket(jsonData) for jsonData in r.json()["data"]]


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
	"""docstring for Bucket"""
	def __init__(self, jsonData):
		self.jsonData           = jsonData
		self.tests              = []
		self.sharedEnvironments = []
		self.dataToFile         = ""


class Test(object):
	def __init__(self, jsonData):
		self.jsonData   = jsonData
		self.testDetail = {}
		self.dataToFile = ""

def createNewFile(textToFile, fileName):
	f = open(runscope.editName(fileName) + ".tf", "w")
	f.write(textToFile)
	f.close()


def createFileTest(textToFile, folderName, fileName):
	f = open(folderName + "/" + runscope.editName(fileName) + ".tf", "w")
	f.write(textToFile)
	f.close()

def createFolder(folderName):
	newName = runscope.editName(folderName) + "_TESTS"
	if not os.path.exists(newName):
		os.makedirs(newName)
	return newName


def initprogressBar(length):
	sys.stdout.write("\n")
	# setup toolbar
	sys.stdout.write("Will creat %d folders with test files\n..." % (length))
	sys.stdout.flush()
	sys.stdout.write("\b\b\b")

def progressBarStep(length, testName, index):
	sys.stdout.write("\033[K") #clear line
	text = "#%s \033[95mCreated '%s.tf' file.\033[0m %s%%" % ("_" * (length - (index+1)), runscope.editName(testName), str(100*(index+1)/length))
	sys.stdout.write(text)
	sys.stdout.flush()
	sys.stdout.write("\b" * (len(text) - 10))
	sys.stdout.flush()


def parse(access_token, numberOfTests):
	api = RunscopeAPI(access_token, numberOfTests)
	buckets = api.getAllBuckets()
	initprogressBar(len(buckets))
	i = 1
	for bucket in buckets:
		folderName = createFolder(bucket.jsonData["name"])
		runscope.createVariables(folderName)
		runscope.createBucket(bucket)
		api.getTestsFromBucket(bucket)
		print("\n%d) Create folder %s and %d test files:" % (i, runscope.editName(bucket.jsonData["name"]), len(bucket.tests)))
		for index, test in enumerate(bucket.tests):
			runscope.createTest(test)
			api.getTestDetail(bucket, test)
			runscope.createTestStep(test, bucket)
			runscope.createSchedule(test)
			runscope.createEnvironment(test, bucket.jsonData["name"])
			createFileTest(test.dataToFile, folderName, test.jsonData["name"])
			progressBarStep(len(bucket.tests), test.jsonData["name"], index)
		api.getSharedEnvironments(bucket)
		runscope.createSharedEnvironment(bucket)
		runscope.createModule(bucket, folderName)
		createNewFile(bucket.dataToFile, bucket.jsonData["name"])
		i += 1
	print("\n\033[92mCompleted!\033[0m")

def main():
	access_token  = input("Enter an access_token for runscope: ")
	numberOfTests = input("How many tests you would like to get from every bucket: ")
	runscope.makeInitFile(access_token)
	parse(access_token, numberOfTests)

main()
