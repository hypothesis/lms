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

    stage("Backend tests") {
        // Run the Postgres test DB in a Docker container.
        postgresContainer = docker.image("postgres:11.5").run("-P -e POSTGRES_DB=lmstest")

        try {
            testApp(image: img, runArgs: "${runArgs} -e TEST_DATABASE_URL=${databaseUrl(postgresContainer)}") {
                installDeps()
                run("make functests-only")
            }
        } finally {
            postgresContainer.stop()
        }
    }

    onlyOnMaster {
        stage("release") {
            releaseApp(image: img)
        }
    }
}

onlyOnMaster {
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
                // deployApp(image: img, app: "lms-ca", env: "prod", region: "ca-central-1")
            }
        )
    }
}

/** Return the URL of the test database in the Postgres container. */
def databaseUrl(postgresContainer) {
    hostIp = sh(script: "facter ipaddress_eth0", returnStdout: true).trim()
    containerPort = sh(script: "docker port ${postgresContainer.id} 5432 | cut -d: -f2", returnStdout: true).trim()
    return "postgresql://postgres@${hostIp}:${containerPort}/lmstest"
}

/**
 * Install some common system dependencies.
 *
 * These are test dependencies that're need to run most of the stages above
 * (tests, lint, ...) but that aren't installed in the production Docker image.
 */
def installDeps() {
    sh "apk add build-base postgresql-dev python3-dev"
    sh "pip3 install -q tox>=3.8.0"
}

/** Run the given command. */
def run(command) {
    sh "cd /var/lib/lms && ${command}"
}
