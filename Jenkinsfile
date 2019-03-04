pipeline {
    agent { label 'docker' }

    environment {
        IMAGE_TAG = env.BRANCH_NAME.replaceFirst('^master$', 'latest')
        GITLAB_TOKEN = credentials('visualization-site-gitlab-token')
        SCANNER_HOME = tool name: 'SonarQube Scanner 3', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
    }

    options {
        gitLabConnection('gitlab')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    triggers {
        gitlab(triggerOnPush: true, triggerOnMergeRequest: true, branchFilterType: 'All')
        cron('H H * * H/3')
    }

    post {
        success {
            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'www', reportFiles: 'index.html', reportName: 'Visualization', reportTitles: ''])
            archiveArtifacts 'nginx.conf,nginx/*.conf,caddy/*.yml'
        }
        unstable {
            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'www', reportFiles: 'index.html', reportName: 'Visualization', reportTitles: ''])
            archiveArtifacts 'nginx.conf,nginx/*.conf,caddy/*.yml'
        }
        failure {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'failed'
        }
        aborted {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'canceled'
        }
        always {
            publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: false, reportDir: 'test/coverage/', reportFiles: 'lcov-report/index.html', reportName: 'Coverage', reportTitles: ''])
            publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: false, reportDir: 'test/results/', reportFiles: 'index.html', reportName: 'Results', reportTitles: ''])
            junit 'test/junit/*.xml'
        }
    }

    stages {
        stage('Start') {
            when {
                expression {
                    currentBuild.rawBuild.getCause(hudson.triggers.TimerTrigger$TimerTriggerCause) == null
                }
            }
            steps {
                updateGitlabCommitStatus name: env.JOB_NAME, state: 'running'
            }
        }
        stage('Build') {
            steps {
                checkout scm
                withCredentials([file(credentialsId: 'visualization-site-config', variable: 'VISUALIZATION_SITE_CONFIGURATION')]) {
                    sh 'cp $VISUALIZATION_SITE_CONFIGURATION config.json'
                    sh 'docker build -t $DOCKER_REGISTRY/gros-visualization-site:$IMAGE_TAG . --build-arg NPM_REGISTRY=$NPM_REGISTRY --build-arg NAVBAR_SCOPE=$NAVBAR_SCOPE --build-arg BRANCH_NAME=$BRANCH_NAME'
                }
            }
        }
        stage('Build test') {
            agent {
                docker {
                    image '$DOCKER_REGISTRY/gros-visualization-site:$IMAGE_TAG'
                    reuseNode true
                }
            }
            steps {
                withCredentials([file(credentialsId: 'upload-server-certificate', variable: 'SERVER_CERTIFICATE')]) {
                    sh 'rm -rf node_modules/'
                    sh 'ln -s /usr/src/app/node_modules .'
                    sh 'cp -r /usr/src/app/node_modules/axe-selenium-python/axe_selenium_python/node_modules/axe-core/ axe-core'
                    sh 'cp $SERVER_CERTIFICATE wwwgros.crt'
                    sh 'SERVER_CERTIFICATE=$PWD/wwwgros.crt npm run pretest -- --env.mixfile=$PWD/webpack.mix.js'
                }
            }
        }
        stage('Test') {
            steps {
                sshagent(['gitlab-clone-auth']) {
                    script {
                        def ret = sh returnStatus: true, script: './run-test.sh'
                        if (ret == 2) {
                            currentBuild.result = 'UNSTABLE'
                        }
                        else if (ret != 0) {
                            currentBuild.result = 'FAILURE'
                            error("Test stage failed with exit code ${ret}")
                        }
                    }
                }
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '${SCANNER_HOME}/bin/sonar-scanner -Dsonar.branch=$BRANCH_NAME -Dsonar.sources=lib,`find repos -name lib -maxdepth 2 -type d | paste -s -d, -`'
                }
            }
        }
        stage('Build production') {
            when { branch '*master' }
            agent {
                docker {
                    image '$DOCKER_REGISTRY/gros-visualization-site:$IMAGE_TAG'
                    reuseNode true
                }
            }
            steps {
                sh 'rm -rf node_modules'
                sh 'ln -s /usr/src/app/node_modules .'
                sh 'npm run production -- --env.mixfile=$PWD/webpack.mix.js'
            }
        }
        stage('Push') {
            when { branch 'master' }
            steps {
                sh 'docker push $DOCKER_REGISTRY/gros-visualization-site:latest'
            }
        }
        stage('Status') {
            when {
                expression {
                    currentBuild.rawBuild.getCause(hudson.triggers.TimerTrigger$TimerTriggerCause) == null
                }
            }
            steps {
                updateGitlabCommitStatus name: env.JOB_NAME, state: 'success'
            }
        }
    }
}
