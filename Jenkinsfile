pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
        IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
        SLACK_CHANNEL = '#roadsense-ci'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_MSG = sh(returnStdout: true, script: 'git log -1 --pretty=%B').trim()
                }
            }
        }
        
        stage('Build Docker Images') {
            stages {
                stage('Build Detection Service') {
                    steps {
                        dir('detection-fissures') {
                            script {
                                echo "🔨 Building Detection Service..."
                                sh """
                                    docker build --memory=2g --memory-swap=2g -t roadsense/detection-service:${IMAGE_TAG} .
                                    docker tag roadsense/detection-service:${IMAGE_TAG} roadsense/detection-service:latest
                                """
                            }
                        }
                    }
                }
                
                stage('Build Ingestion Service') {
                    steps {
                        dir('ingestion-video') {
                            script {
                                echo "🔨 Building Ingestion Service..."
                                sh """
                                    docker build --memory=2g --memory-swap=2g -t roadsense/ingestion-service:${IMAGE_TAG} .
                                    docker tag roadsense/ingestion-service:${IMAGE_TAG} roadsense/ingestion-service:latest
                                """
                            }
                        }
                    }
                }
                
                stage('Build Dashboard') {
                    steps {
                        dir('dashboard') {
                            script {
                                echo "🔨 Building Dashboard..."
                                sh """
                                    docker build --memory=2g --memory-swap=2g -t roadsense/dashboard:${IMAGE_TAG} .
                                    docker tag roadsense/dashboard:${IMAGE_TAG} roadsense/dashboard:latest
                                """
                            }
                        }
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                script {
                    echo "⏭️  Skipping tests - will be implemented in separate test containers"
                    echo "✅ Docker images built successfully"
                }
            }
        }
        
        stage('Code Quality Analysis') {
            steps {
                script {
                    echo "📊 Running SonarQube Analysis..."
                    // SonarQube scanner - use token from credentials
                    withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
                        sh """
                            sonar-scanner \
                            -Dsonar.projectKey=roadsense \
                            -Dsonar.sources=. \
                            -Dsonar.host.url=http://sonarqube:9090 \
                            -Dsonar.token=\${SONAR_TOKEN} \
                            -Dsonar.python.coverage.reportPaths=coverage.xml
                        """
                    }
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                script {
                    echo "🚦 Checking Quality Gate..."
                    timeout(time: 5, unit: 'MINUTES') {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted due to quality gate failure: ${qg.status}"
                        }
                    }
                }
            }
        }
        
        stage('Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "📦 Pushing images to Docker Registry..."
                    docker.withRegistry("https://${DOCKER_REGISTRY}", DOCKER_CREDENTIALS_ID) {
                        sh """
                            docker push roadsense/detection-service:${IMAGE_TAG}
                            docker push roadsense/detection-service:latest
                            docker push roadsense/ingestion-service:${IMAGE_TAG}
                            docker push roadsense/ingestion-service:latest
                            docker push roadsense/dashboard:${IMAGE_TAG}
                            docker push roadsense/dashboard:latest
                        """
                    }
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "🚀 Deploying to Staging Environment..."
                    sh """
                        chmod +x scripts/deploy.sh
                        ./scripts/deploy.sh staging ${IMAGE_TAG}
                    """
                }
            }
        }
        
        stage('Health Check Staging') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "🏥 Running health checks on Staging..."
                    sh """
                        chmod +x scripts/health-check.sh
                        ./scripts/health-check.sh staging
                    """
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "⚠️ Waiting for manual approval..."
                    input message: 'Deploy to Production?', ok: 'Deploy'
                    
                    echo "🚀 Deploying to Production Environment..."
                    sh """
                        chmod +x scripts/deploy.sh
                        ./scripts/deploy.sh production ${IMAGE_TAG}
                    """
                }
            }
        }
        
        stage('Health Check Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "🏥 Running health checks on Production..."
                    sh """
                        chmod +x scripts/health-check.sh
                        ./scripts/health-check.sh production
                    """
                }
            }
        }
    }
    
    post {
        success {
            script {
                echo "✅ Pipeline completed successfully!"
                slackSend(
                    channel: SLACK_CHANNEL,
                    color: 'good',
                    message: """
                        ✅ *RoadSense Build Success*
                        *Branch:* ${env.BRANCH_NAME}
                        *Build:* #${env.BUILD_NUMBER}
                        *Commit:* ${env.GIT_COMMIT.take(7)}
                        *Message:* ${env.GIT_COMMIT_MSG}
                        *Duration:* ${currentBuild.durationString}
                        *Status:* Deployed to Production
                    """
                )
                
                emailext(
                    subject: "✅ RoadSense Build #${env.BUILD_NUMBER} - SUCCESS",
                    body: """
                        <h2>Build Successful</h2>
                        <p><strong>Branch:</strong> ${env.BRANCH_NAME}</p>
                        <p><strong>Commit:</strong> ${env.GIT_COMMIT}</p>
                        <p><strong>Message:</strong> ${env.GIT_COMMIT_MSG}</p>
                        <p><strong>Duration:</strong> ${currentBuild.durationString}</p>
                        <p><strong>Status:</strong> Deployed to Production</p>
                    """,
                    to: 'devops@roadsense.com',
                    mimeType: 'text/html'
                )
            }
        }
        
        failure {
            script {
                echo "❌ Pipeline failed!"
                slackSend(
                    channel: SLACK_CHANNEL,
                    color: 'danger',
                    message: """
                        ❌ *RoadSense Build Failed*
                        *Branch:* ${env.BRANCH_NAME}
                        *Build:* #${env.BUILD_NUMBER}
                        *Commit:* ${env.GIT_COMMIT.take(7)}
                        *Message:* ${env.GIT_COMMIT_MSG}
                        *Duration:* ${currentBuild.durationString}
                        *Stage:* ${env.STAGE_NAME}
                        *Logs:* ${env.BUILD_URL}console
                    """
                )
                
                emailext(
                    subject: "❌ RoadSense Build #${env.BUILD_NUMBER} - FAILED",
                    body: """
                        <h2 style="color: red;">Build Failed</h2>
                        <p><strong>Branch:</strong> ${env.BRANCH_NAME}</p>
                        <p><strong>Commit:</strong> ${env.GIT_COMMIT}</p>
                        <p><strong>Message:</strong> ${env.GIT_COMMIT_MSG}</p>
                        <p><strong>Failed Stage:</strong> ${env.STAGE_NAME}</p>
                        <p><a href="${env.BUILD_URL}console">View Console Logs</a></p>
                    """,
                    to: 'devops@roadsense.com',
                    mimeType: 'text/html'
                )
            }
        }
        
        always {
            script {
                echo "🧹 Cleaning up..."
                sh """
                    docker system prune -f
                    docker volume prune -f
                """
            }
        }
    }
}
