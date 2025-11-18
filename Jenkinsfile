pipeline {
    agent any
    environment {
        // Define remote server details
        REMOTE_USER = 'airflow'
        REMOTE_HOST = 'logsmanager-airflow-scheduler-1'
        REMOTE_PATH = '/opt/airflow/dags'
    }


    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                echo 'Setting up Python environment...'
                sh '''
                    python3 -m venv ${VENV_NAME}
                    . ${VENV_NAME}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                echo 'Running code linting...'
                sh '''
                    . ${VENV_NAME}/bin/activate
                    flake8 src tests --max-line-length=88 --exclude=venv
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Running unit tests...'
                sh '''
                    . ${VENV_NAME}/bin/activate
                    pytest tests/ -v --cov=src --cov-report=xml --cov-report=html --cov-report=term
                '''
            }
        }

        stage('Code Quality') {
            steps {
                echo 'Running code quality checks...'
                sh '''
                    . ${VENV_NAME}/bin/activate
                    pylint src --fail-under=8.0 || true
                '''
            }
        }

        stage('Deploy') {
            steps {
                script {
                    // Use Jenkins credentials for SSH if configured
                    // Example: withCredentials([sshUserPrivateKey(credentialsId: 'ssh-key-id', keyFileVariable: 'SSH_KEY')]) { ... }
                    
                    sh """
                        echo "Transferring DAG files to remote server..."
                        scp -r DAG/* ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}
                    """
                }
            }
        }



        stage('Archive') {
            steps {
                echo 'Archiving artifacts...'
                archiveArtifacts artifacts: 'dist/*', fingerprint: true
                archiveArtifacts artifacts: 'htmlcov/**/*', fingerprint: true
            }
        }
    }

    post {
        always {
            echo 'Cleaning up...'
            junit allowEmptyResults: true, testResults: '**/test-results/*.xml'
            publishHTML([
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
            ])
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}

