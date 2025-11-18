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

        stage('Deploy') {
            steps {
                script {
                    // Use Jenkins credentials for SSH if configured
                    // Example: withCredentials([sshUserPrivateKey(credentialsId: 'ssh-key-id', keyFileVariable: 'SSH_KEY')]) { ... }
                    
                    // sh """
                    //     echo "Transferring DAG files to remote server..."
                    //     scp -r DAG/* ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}
                    // """
                    sh """
                    cp DAG/* /var/jenkins_home/airflow_dags 
                    """
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}

