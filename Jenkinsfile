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

    // Run each of the stages in parallel.
    parallel failFast: true,
    "Formatting": {
        stage("Formatting") {
            testApp(image: img, runArgs: runArgs) {
                installDeps()
                run("make checkformatting")
            }
        }
    },
    "Docstrings": {
        stage("Docstrings") {
            testApp(image: img, runArgs: runArgs) {
                installDeps()
                run("make checkdocstrings")
            }
        }
    },
    "Backend lint": {
        stage("Backend lint") {
            testApp(image: img, runArgs: runArgs) {
                installDeps()
                run("make backend-lint")
            }
        }
    },
    "Backend tests": {
        stage("Backend tests") {
            // Run the Postgres test DB in a Docker container.
            postgresContainer = docker.image("postgres:9.4").run("-P -e POSTGRES_DB=lmstest")

            try {
                testApp(image: img, runArgs: "${runArgs} -e TEST_DATABASE_URL=${databaseUrl(postgresContainer)} -e CODECOV_TOKEN=${credentials('LMS_CODECOV_TOKEN')}") {
                    installDeps()
                    run("make backend-tests coverage codecov")
                }
            } finally {
                postgresContainer.stop()
            }
        }
    },
    "Frontend lint": {
        stage("Frontend lint") {
            testApp(image: img, runArgs: runArgs) {
                installDeps()
                sh "apk add yarn"
                run("make frontend-lint")
            }
        }
    },
    "Frontend tests": {
        stage("Frontend tests") {
            workspace = pwd()
            // The frontend tests use a node Docker image because they're
            // incompatible with the hypothesis/lms image.
            docker.image("node:10-stretch").inside("${runArgs} -e HOME=${workspace}") {
                sh "make frontend-tests"
            }
        }
    }

    onlyOnMaster {
        stage("release") {
            releaseApp(image: img)
        }
    }
}

deployToQAAndProd()

/**
 * If this is the master branch then deploy the app to QA and prod.
 */
def deployToQAAndProd() {
    onlyOnMaster {
        milestone()
        stage("qa deploy") {
            deployApp(image: img, app: "lms", env: "qa")
        }

        milestone()
        stage("prod deploy") {
            input(message: "Deploy to prod?")
            milestone()
            deployApp(image: img, app: "lms", env: "prod")
        }
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
