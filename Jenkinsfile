/**
 * This app's Jenkins Pipeline.
 *
 * This is written in Jenkins Scripted Pipeline language.
 * For docs see:
 * https://jenkins.io/doc/book/pipeline/syntax/#scripted-pipeline
*/

// Import the Hypothesis shared pipeline library, which is defined in this
// repo: https://github.com/hypothesis/pipeline-library
@Library("pipeline-library") _

// The the built hypothesis/lms Docker image.
def img

node {
    // The args that we'll pass to Docker run each time we run the Docker
    // image.
    runArgs = "-u root -e SITE_PACKAGES=true"

    stage("Build") {
        // Checkout the commit that triggered this pipeline run.
        checkout scm
        // Build the Docker image.
        img = buildApp(name: "hypothesis/lms")
    }

    onlyOnMain {
        stage("release") {
            releaseApp(image: img)
        }
    }
}

onlyOnMain {
    milestone()
    stage("qa deploy") {
        deployApp(image: img, app: "lms", env: "qa", region: "us-west-1")
    }

    milestone()
    stage("approval") {
        input(message: "Proceed to production deploy?")
    }

    milestone()
    stage("prod Deploy") {
        parallel(
            us: {
                deployApp(image: img, app: "lms", env: "prod", region: "us-west-1")
            },
            ca: {
		// Workaround to ensure all parallel builds happen. See https://hypothes-is.slack.com/archives/CR3E3S7K8/p1625041642057400
                sleep 2
                deployApp(image: img, app: "lms-ca", env: "prod", region: "ca-central-1")
            }
        )
    }
}
