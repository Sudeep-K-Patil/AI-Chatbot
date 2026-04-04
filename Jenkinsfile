pipeline {
    agent any

    environment {
        IMAGE_NAME = 'ai-chatbot'
        CONTAINER_NAME = 'ai-chatbot-jenkins'
        APP_PORT = '5000'
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
                      --env-file .env ^
                      -e OLLAMA_HOST=http://host.docker.internal:11434 ^
                      %IMAGE_NAME%
                '''
            }
            post {
                always {
                    bat 'docker logs %CONTAINER_NAME%'
                    bat 'docker rm -f %CONTAINER_NAME% 2>NUL'
                }
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
    }

}
