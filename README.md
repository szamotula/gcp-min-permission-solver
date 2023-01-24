# gcp-min-permission-solver

This script finds the minimum permissions required to perform a task in GCP.  Given a GCP cloud function
it will find the minimum set of permissions required for that cloud function to succeed.

## Motivation

My team needed to create a new pub/sub subscription from within a GCP cloud function.  We assigned the pub/sub admin
role to the cloud function service account, but it failed with a permissions error.  We then assigned the editor
role and it succeeded.  There was a mysterious permission required to create a pub/sub subscription.

We were unable to find the missing permission working with GCP support, so I wrote this tool to help us find it.  It 
turns out that the missing permission was 'iam.serviceAccounts.actAs'.

## Usage

### Setup

* Create a Local Service Account:
  * Create a service account that will be used to run this tool.  It requires the following roles:
    * `roles/cloudfunctions.admin`
    * `roles/storage.admin`
    * `roles/iam.roleAdmin`
    * `roles/iam.serviceAccountAdmin`
    * `roles/resourcemanager.projectIamAdmin`
  * Download the [Service Account Key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#get-key)
    for your service account.
    * Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to the path of the downloaded key.
* Create your Cloud Function:
  * Create a [Google Cloud Function](https://cloud.google.com/functions/) with an HTTPS trigger that performs your 
  desired task.
  * Assign a custom service account to the cloud function.  This service account will be modified to test permissions.
  * If your cloud function has side effects when run successfully or unsuccessfully, implement clean up in 
  `__clean_up()` in [permission_tester.py](./src/permission_tester.py) and give any additional roles needed to your
  service account.
* Install the required dependencies: `pip install -r requirements.txt`

### Running the tool

* Run the script: `python solver.py projects/<project>/locations/<location>/functions/<function>`
  * This tool will modify the service account assigned to the cloud function and run the cloud function many times.  Make 
  sure you are using a service account that is not used for anything else, and that any side effects of running
  your cloud function successfully or unsuccessfully are cleaned up each time.
  * When we update permissions in GCP, it takes about a minute for the changes to propagate.  The script will wait two
  minutes after each permission update before running the function.  This means the script takes a few hours
  to complete.
  * If you would like monitor more of the process while it runs, set the log level to info with the arg `-l INFO`.