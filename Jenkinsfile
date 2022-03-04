pipeline {
    agent { label 'docker-compose' }

    parameters {
        string(name: 'VISUALIZATION_ORGANIZATION', defaultValue: "${env.VISUALIZATION_ORGANIZATION}", description: 'Organization to build for')
        string(name: 'NAVBAR_SCOPE', defaultValue: "", description: 'Organization scope to use in navigation bar (keep empty to use generic style)')
        booleanParam(name: 'VISUALIZATION_COMBINED', defaultValue: true, description: 'Build for combined visualization')
    }

    environment {
        IMAGE_TAG = env.BRANCH_NAME.replaceFirst('^master$', 'latest')
        VISUALIZATION_IMAGE = "gros-visualization-site:$IMAGE_TAG"
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
            archiveArtifacts 'nginx.conf,nginx/*.conf,caddy/*.yml'
        }
        unstable {
            archiveArtifacts 'nginx.conf,nginx/*.conf,caddy/*.yml'
        }
        failure {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'failed'
        }
        aborted {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'canceled'
        }
        always {
            publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: false, reportDir: 'test/coverage/', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
            publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: false, reportDir: 'test/results/', reportFiles: 'index.html', reportName: 'Results', reportTitles: ''])
            publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: false, reportDir: 'test/accessibility/', reportFiles: 'index.html', reportName: 'Accessiblity', reportTitles: ''])
            publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: false, reportDir: 'test/owasp-dep/', reportFiles: 'dependency-check-report.html', reportName: 'Dependencies', reportTitles: ''])
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
                    sh 'docker build -t $DOCKER_REPOSITORY/$VISUALIZATION_IMAGE . --build-arg NPM_REGISTRY=$NPM_REGISTRY'
                    sh 'docker ps -q --filter "volume=$BRANCH_NAME-visualization-site-modules" | xargs --no-run-if-empty docker stop'
                    sh 'docker volume rm -f "$BRANCH_NAME-visualization-site-modules"'
                }
            }
        }
        stage('Push') {
            when { branch 'master' }
            steps {
                withDockerRegistry(credentialsId: 'docker-credentials', url: env.DOCKER_URL) {
                    sh 'docker push $DOCKER_REPOSITORY/$VISUALIZATION_IMAGE'
                }
            }
        }
        stage('Build test') {
            agent {
                docker {
                    image '$VISUALIZATION_IMAGE'
                    registryUrl "${env.DOCKER_URL}"
                    registryCredentialsId 'docker-credentials'
                    reuseNode true
                    args '-v $BRANCH_NAME-visualization-site-modules:/usr/src/app/node_modules'
                }
            }
            steps {
                withCredentials([file(credentialsId: 'upload-server-certificate', variable: 'SERVER_CERTIFICATE')]) {
                    sh 'rm -rf node_modules/'
                    sh 'ln -s /usr/src/app/node_modules .'
                    sh 'cp -r /usr/src/app/node_modules/axe-core/ axe-core'
                    sh 'cp $SERVER_CERTIFICATE wwwgros.crt'
                    sh "SERVER_CERTIFICATE=$WORKSPACE/wwwgros.crt VISUALIZATION_ORGANIZATION=${params.VISUALIZATION_ORGANIZATION} VISUALIZATION_COMBINED=${params.VISUALIZATION_COMBINED} NAVBAR_SCOPE=${params.NAVBAR_SCOPE} MIX_FILE=$WORKSPACE/webpack.mix.js npm run pretest"
                    stash includes: 'visualization_names.txt', name: 'visualization_names'
                }
            }
        }
        stage('Test') {
            steps {
                withCredentials([file(credentialsId: 'visualization-site-config', variable: 'VISUALIZATION_SITE_CONFIGURATION'), file(credentialsId: 'prediction-site-config', variable: 'PREDICTION_CONFIGURATION')]) {
                    withDockerRegistry(credentialsId: 'docker-credentials', url: env.DOCKER_URL) {
                        sshagent(['gitlab-clone-auth']) {
                            script {
                                def ret = sh returnStatus: true, script: "VISUALIZATION_ORGANIZATION=${params.VISUALIZATION_ORGANIZATION} VISUALIZATION_COMBINED=${params.VISUALIZATION_COMBINED} ./run-test.sh"
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
            }
        }
        stage('Collect results') {
            agent {
                docker {
                    image '$VISUALIZATION_IMAGE'
                    registryUrl "${env.DOCKER_URL}"
                    registryCredentialsId 'docker-credentials'
                    reuseNode true
                }
            }
            steps {
                sh 'npm run nyc-report'
                sh 'npm run axe-report'
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withPythonEnv('System-CPython-3') {
                    pysh 'python -m pip install pylint'
                    pysh 'python -m pylint test/suite --exit-zero --reports=n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" -d duplicate-code > test/pylint-report.txt'
                }
                withSonarQubeEnv('SonarQube') {
                    sh 'if [ -d repos/prediction-site/test ]; then cp test/coverage/lcov.info repos/prediction-site/test/coverage/lcov.info; grep -E "^test/suite/test_prediction_site.py:" test/pylint-report.txt > repos/prediction-site/test/pylint-report.txt; ${SCANNER_HOME}/bin/sonar-scanner -Dproject.settings=repos/prediction-site/sonar-project.properties -Dsonar.projectKey=prediction-site:master -Dsonar.projectName="Prediction site master" -Dsonar.projectBaseDir=repos/prediction-site; fi'
                    sh '${SCANNER_HOME}/bin/sonar-scanner -Dsonar.projectKey=visualization-site:$BRANCH_NAME -Dsonar.projectName="Visualization site $BRANCH_NAME" -Dsonar.sources=lib,`find repos -name lib -maxdepth 2 -type d | paste -s -d, -`'
                }
            }
        }
        stage('Build production') {
            when { branch '*master' }
            agent {
                docker {
                    image '$VISUALIZATION_IMAGE'
                    registryUrl "${env.DOCKER_URL}"
                    registryCredentialsId 'docker-credentials'
                    reuseNode true
                }
            }
            steps {
                sh 'rm -rf node_modules'
                sh 'ln -s /usr/src/app/node_modules .'
                sh "VISUALIZATION_ORGANIZATION=${params.VISUALIZATION_ORGANIZATION} VISUALIZATION_COMBINED=${params.VISUALIZATION_COMBINED} NAVBAR_SCOPE=${params.NAVBAR_SCOPE} MIX_FILE=$WORKSPACE/webpack.mix.js npm run production"
                publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'www', reportFiles: 'index.html', reportName: 'Visualization', reportTitles: ''])
            }
        }
        stage('Copy') {
            when { branch 'master' }
            agent {
                label 'publish'
            }
            steps {
                checkout scm
                withCredentials([file(credentialsId: 'visualization-site-config', variable: 'VISUALIZATION_SITE_CONFIGURATION')]) {
                    sh 'cp $VISUALIZATION_SITE_CONFIGURATION config.json'
                    unstash 'visualization_names'
                    sh './copy.sh'
                }
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
