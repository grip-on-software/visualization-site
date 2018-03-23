pipeline {
    agent { label 'docker' }

    environment {
        SCANNER_HOME = tool name: 'SonarQube Scanner 3', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
    }

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
                sh 'docker build -t $DOCKER_REGISTRY/gros-visualization-site . --build-arg NPM_REGISTRY=$NPM_REGISTRY --build-arg NAVBAR_SCOPE=$NAVBAR_SCOPE'
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
                sh 'cp /usr/src/app/www/*.{js,css,html} $PWD/www/'
                sh 'cp -rf /usr/src/app/www/fonts/ $PWD/www/fonts/'
            }
        }
        stage('Test') {
            steps {
                updateGitlabCommitStatus name: env.JOB_NAME, state: 'running'
                sh './run-test.sh'
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '${SCANNER_HOME}/bin/sonar-scanner -Dsonar.branch=$BRANCH_NAME'
                }
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
