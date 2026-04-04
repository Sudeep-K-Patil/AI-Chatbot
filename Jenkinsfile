pipeline {
    agent any

    environment {
        IMAGE_NAME = 'ai-chatbot'
        CONTAINER_NAME = 'ai-chatbot-jenkins'
        APP_PORT = '5000'
        OLLAMA_MODEL = 'llama3.2'
        FLASK_SECRET_KEY = 'jenkins-local-secret'
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
                bat 'docker build -t %IMAGE_NAME% .'
            }
        }

        stage('Run Container') {
            steps {
                bat '''
                    docker rm -f %CONTAINER_NAME% 2>NUL
                    docker run -d --name %CONTAINER_NAME% ^
                      -p %APP_PORT%:5000 ^
                      -e OLLAMA_HOST=http://host.docker.internal:11434 ^
                      -e OLLAMA_MODEL=%OLLAMA_MODEL% ^
                      -e FLASK_SECRET_KEY=%FLASK_SECRET_KEY% ^
                      %IMAGE_NAME%
                '''
            }
        }

        stage('Health Check') {
            steps {
                powershell '''
                    $maxAttempts = 12
                    for ($i = 1; $i -le $maxAttempts; $i++) {
                        try {
                            $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/health" -UseBasicParsing -TimeoutSec 5
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

        stage('Cleanup') {
            steps {
                bat 'docker logs %CONTAINER_NAME% 2>NUL'
                bat 'docker rm -f %CONTAINER_NAME% 2>NUL'
            }
        }
    }

}
