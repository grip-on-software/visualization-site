pipeline {
    agent { label 'docker' }

    options {
        gitLabConnection('gitlab')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    triggers {
        gitlab(triggerOnPush: true, triggerOnMergeRequest: true, branchFilterType: 'All')
    }

    post {
        success {
            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'www', reportFiles: 'index.html', reportName: 'Visualization', reportTitles: ''])
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'success'
        }
        failure {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'failed'
        }
        aborted {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'canceled'
        }
    }

    stages {
        stage('Build') {
            steps {
                updateGitlabCommitStatus name: env.JOB_NAME, state: 'running'
                sh 'docker build -t $DOCKER_REGISTRY/gros-visualization-site . --build-arg NPM_REGISTRY=$NPM_REGISTRY'
            }
        }
        stage('Extract') {
            agent {
                docker {
                    image '$DOCKER_REGISTRY/gros-visualization-site'
                    reuseNode true
                }
            }
            steps {
                sh 'cp /usr/src/app/www/bundle.js $PWD/www/bundle.js'
                sh 'cp /usr/src/app/www/main.css $PWD/www/main.css'
            }
        }
        stage('Test') {
            steps {
                updateGitlabCommitStatus name: env.JOB_NAME, state: 'running'
                sh './run-test.sh'
            }
        }
        stage('Push') {
            when { branch 'master' }
            steps {
                sh 'docker push $DOCKER_REGISTRY/gros-visualization-site:latest'
            }
        }
    }
}
