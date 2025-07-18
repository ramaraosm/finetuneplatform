import React, { useState, useEffect, useRef } from 'react'; // Import useRef
import axios from 'axios';

const JobStatus = ({ initialJob, apiUrl }) => {
    const [job, setJob] = useState(initialJob);
    const intervalRef = useRef(null); // Create a ref to store the interval ID

    useEffect(() => {
        // Immediately set the job when initialJob changes (e.g., a new job is submitted)
        setJob(initialJob);

        // Clear any existing interval when initialJob changes
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        const pollStatus = async (currentJobId) => {
            try {
                const response = await axios.get(`${apiUrl}/jobs/${currentJobId}`);
                const updatedJob = response.data;
                setJob(updatedJob);

                // If the job is no longer QUEUED or RUNNING, clear the interval
                if (updatedJob.status !== 'QUEUED' && updatedJob.status !== 'RUNNING') {
                    if (intervalRef.current) {
                        clearInterval(intervalRef.current);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch job status:", error);
                // In case of an error, you might want to stop polling as well
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                }
            }
        };

        // Start polling if the initial job status is QUEUED or RUNNING
        if (initialJob.status === 'QUEUED' || initialJob.status === 'RUNNING') {
            // Immediately poll once
            pollStatus(initialJob.id);

            // Set up the interval for subsequent polls
            intervalRef.current = setInterval(() => {
                // Pass the current job ID to pollStatus
                pollStatus(job.id); // It's safer to use a ref or ensure the ID is always current if not in dependencies
                                    // However, initialJob.id is stable here.
            }, 5000); // Poll every 5 seconds
        }

        // Cleanup function to clear the interval when the component unmounts
        // or when initialJob changes and a new interval is set up
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [initialJob, apiUrl]); // Dependencies: only re-run effect when initialJob or apiUrl changes


    const getStatusClassName = () => {
        switch (job.status) {
            case 'COMPLETED': return 'success';
            case 'FAILED': return 'error';
            case 'RUNNING': return 'running';
            default: return '';
        }
    };

    return (
        <div className="status-box">
            <h3>Job Status</h3>
            <p><strong>Job ID:</strong> {job.id}</p>
            <p><strong>Model Name:</strong> {job.new_model_name}</p>
            <p>
                <strong>Status:</strong>{' '}
                <span className={`status-message ${getStatusClassName()}`}>{job.status}</span>
            </p>
            {job.status === 'COMPLETED' && (
                <p className="status-message success">
                    Success! Your model is available at:{' '}
                    <a href={`https://huggingface.co/${process.env.REACT_APP_HUGGING_FACE_USERNAME}/Finetuned-${job.new_model_name}`} target="_blank" rel="noopener noreferrer">
                        Hugging Face Hub
                    </a>
                </p>
            )}
            {job.status === 'FAILED' && <p className="status-message error"><strong>Error:</strong> {job.error_message}</p>}
        </div>
    );
};

export default JobStatus;