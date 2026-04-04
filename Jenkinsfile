pipeline {
    agent any

    environment {
        IMAGE_NAME = 'ai-chatbot'
        TEST_CONTAINER_NAME = 'ai-chatbot-test'
        DEPLOY_CONTAINER_NAME = 'ai-chatbot-app'
        APP_PORT = '5000'
        TEST_PORT = '5050'
        OLLAMA_MODEL = 'llama3.2'
        FLASK_SECRET_KEY = 'jenkins-local-secret'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                retry(3) {
                    checkout([
                        $class: 'GitSCM',
                        branches: scm.branches ?: [[name: '*/main']],
                        doGenerateSubmoduleConfigurations: false,
                        extensions: [
                            [$class: 'CloneOption', shallow: true, depth: 1, noTags: false, timeout: 20]
                        ],
                        userRemoteConfigs: scm.userRemoteConfigs
                    ])
                }
                bat 'git rev-parse --abbrev-ref HEAD'
                bat 'git rev-parse --short HEAD'
            }
        }

        stage('Build Image') {
            steps {
                bat 'docker build -t %IMAGE_NAME%:%IMAGE_TAG% -t %IMAGE_NAME%:latest .'
            }
        }

        stage('Run Test Container') {
            steps {
                bat '''
                    docker rm -f %TEST_CONTAINER_NAME% 2>NUL
                    docker run -d --name %TEST_CONTAINER_NAME% ^
                      -p %TEST_PORT%:5000 ^
                      -e OLLAMA_HOST=http://host.docker.internal:11434 ^
                      -e OLLAMA_MODEL=%OLLAMA_MODEL% ^
                      -e FLASK_SECRET_KEY=%FLASK_SECRET_KEY% ^
                      %IMAGE_NAME%:%IMAGE_TAG%
                '''
            }
        }

        stage('Health Check') {
            steps {
                powershell '''
                    $maxAttempts = 12
                    for ($i = 1; $i -le $maxAttempts; $i++) {
                        try {
                            $response = Invoke-WebRequest -Uri "http://127.0.0.1:5050/health" -UseBasicParsing -TimeoutSec 5
                            if ($response.StatusCode -eq 200) {
                                Write-Host "Health check passed."
                                exit 0
                            }
                        } catch {
                            Start-Sleep -Seconds 5
                        }
                    }
                    throw "Health check failed after waiting for the container to start."
                '''
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                    docker rm -f %DEPLOY_CONTAINER_NAME% 2>NUL
                    docker run -d --name %DEPLOY_CONTAINER_NAME% ^
                      -p %APP_PORT%:5000 ^
                      -e OLLAMA_HOST=http://host.docker.internal:11434 ^
                      -e OLLAMA_MODEL=%OLLAMA_MODEL% ^
                      -e FLASK_SECRET_KEY=%FLASK_SECRET_KEY% ^
                      %IMAGE_NAME%:%IMAGE_TAG%
                '''
            }
        }
    }

    post {
        always {
            bat 'docker logs %TEST_CONTAINER_NAME% 2>NUL'
            bat 'docker rm -f %TEST_CONTAINER_NAME% 2>NUL'
        }
        success {
            echo 'Deployment completed. App should now be running on port 5000.'
        }
        failure {
            echo 'Deployment failed. Existing deployed container was not replaced unless the deploy stage had already started.'
            bat 'docker ps -a'
            bat 'docker logs %DEPLOY_CONTAINER_NAME% 2>NUL'
        }
    }
}
