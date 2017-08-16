#!groovy

@Library('pipeline-library') _

def img

node {
    stage('build') {
        checkout(scm)
        img = buildApp(name: 'hypothesis/lti')
    }

    stage('test') {
        hostIp = sh(script: 'facter ipaddress_eth0', returnStdout: true).trim()

        postgres = docker.image('postgres:9.4').run('-P -e POSTGRES_DB=ltitest')
        databaseUrl = "postgresql://postgres@${hostIp}:${containerPort(postgres, 5432)}/ltitest"

        try {
            testApp(image: img, runArgs: "-u root -e TEST_DATABASE_URL=${databaseUrl}") {
                sh 'apk-install build-base postgresql-dev python-dev'
                sh 'pip install -q tox'
                sh 'cd /var/lib/lti && tox'
            }
        } finally {
            postgres.stop()
        }
    }

    onlyOnMaster {
        stage('release') {
            releaseApp(image: img)
        }
    }
}

def containerPort(container, port) {
    return sh(
        script: "docker port ${container.id} ${port} | cut -d: -f2",
        returnStdout: true
    ).trim()
}
