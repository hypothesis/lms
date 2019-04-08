#!groovy

@Library('pipeline-library') _

def img

node {
    stage('build') {
        checkout(scm)
        img = buildApp(name: 'hypothesis/lms')
    }

    stage('test') {
        hostIp = sh(script: 'facter ipaddress_eth0', returnStdout: true).trim()

        postgres = docker.image('postgres:9.4').run('-P -e POSTGRES_DB=lmstest')
        databaseUrl = "postgresql://postgres@${hostIp}:${containerPort(postgres, 5432)}/lmstest"

        try {
            testApp(image: img, runArgs: "-u root -e TEST_DATABASE_URL=${databaseUrl} -e CODECOV_TOKEN=${credentials('LMS_CODECOV_TOKEN')}") {
                sh 'apk add build-base postgresql-dev python3-dev yarn'
                sh 'pip3 install -q tox>=3.8.0'

                // Hack to work around a race condition and make sure that
                // .tox/.tox/bin/tox gets created before any of the parallelised
                // `make` commands below try to access it.
                sh 'cd /var/lib/lms && tox -e py36 --notest'

                sh 'cd /var/lib/lms && make checkformatting lint backend-tests'
                sh 'cd /var/lib/lms && make coverage codecov'
            }
        } finally {
            postgres.stop()
        }

        nodeEnv = docker.image("node:10-stretch")
        workspace = pwd()
        nodeEnv.inside("-u root -e HOME=${workspace}") {
            sh 'make frontend-tests'
        }
    }

    onlyOnMaster {
        stage('release') {
            releaseApp(image: img)
        }
    }
}

onlyOnMaster {
    milestone()
    stage('qa deploy') {
        deployApp(image: img, app: 'lms', env: 'qa')
    }

    milestone()
    stage('prod deploy') {
        input(message: "Deploy to prod?")
        milestone()
        deployApp(image: img, app: 'lms', env: 'prod')
    }
}

def containerPort(container, port) {
    return sh(
        script: "docker port ${container.id} ${port} | cut -d: -f2",
        returnStdout: true
    ).trim()
}
