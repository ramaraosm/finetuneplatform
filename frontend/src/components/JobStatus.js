import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// InferencePage Component
const InferencePage = ({ baseApiUrl, base_model, hf_repo, onBack }) => {
    const [prompt, setPrompt] = useState('');
    const [generatedText, setGeneratedText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [currentInferenceJobId, setCurrentInferenceJobId] = useState(null);
    const [inferenceStatus, setInferenceStatus] = useState('');

    const pollingIntervalRef = useRef(null); // Ref to store the interval ID

    // Function to submit the inference request
    const handleSubmitInference = async () => {
        setIsLoading(true);
        setError('');
        setGeneratedText('');
        setCurrentInferenceJobId(null); // Reset job ID for a new request
        setInferenceStatus('');

        try {
            // Send the initial inference request.
            // Note: The backend generates the job_id (request_id), so we don't send one.
            const response = await axios.post(`${baseApiUrl}/inference/generate_text`, {
                base_model: base_model,
                prompt: prompt,
                huggingface_repo: hf_repo,
            }, {
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = response.data; // Axios automatically parses JSON

            if (result && result.job_id && result.status) {
                setCurrentInferenceJobId(result.job_id);
                setInferenceStatus(result.status);
                console.log("Inference request submitted successfully. Job ID:", result.job_id);
            } else {
                setError("No job ID or status received, or unexpected response structure from backend.");
                console.error("Unexpected backend response for submission:", result);
            }
        } catch (err) {
            console.error("Error during inference submission:", err);
            if (err.response) {
                setError(`Failed to submit inference request: ${err.response.status} - ${err.response.data.detail || err.response.statusText}`);
            } else if (err.request) {
                setError(`Failed to submit inference request: No response from server. Ensure your Python backend is running and accessible.`);
            } else {
                setError(`Failed to submit inference request: ${err.message}`);
            }
            setIsLoading(false); // Stop loading on submission error
        }
    };

    // Effect for polling the inference status
    useEffect(() => {
        if (currentInferenceJobId) {
            // Clear any existing interval before starting a new one
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
            }

            // Start polling
            pollingIntervalRef.current = setInterval(async () => {
                try {
                    const response = await axios.get(`${baseApiUrl}/inference/${currentInferenceJobId}`);
                    const updatedJob = response.data;

                    setInferenceStatus(updatedJob.status);

                    if (updatedJob.status === 'COMPLETED_INFERENCE' || updatedJob.status === 'COMPLETED') {
                        // Assuming updatedJob.result contains the generated text
                       // updatedJob.result will now directly be the string or null
                        if (typeof updatedJob.result === 'string' && updatedJob.result) {
                            setGeneratedText(updatedJob.result); // Set the string directly
                            console.log("Inference completed. Output:", updatedJob.result);
                        } else {
                            setError("Inference completed, but no valid text output was received.");
                            setGeneratedText("No valid inference output found."); // Provide a fallback
                            console.error("Inference completed with unexpected result:", updatedJob.result);
                        }
                        setIsLoading(false);
                        clearInterval(pollingIntervalRef.current); // Stop polling
                        pollingIntervalRef.current = null;
                        console.log("Inference completed. Result:", updatedJob.result);
                    } else if (updatedJob.status === 'FAILED_INFERENCE' || updatedJob.status === 'FAILED') {
                        setError(`Inference failed: ${updatedJob.error_message || 'Unknown error'}`);
                        setIsLoading(false);
                        clearInterval(pollingIntervalRef.current); // Stop polling
                        pollingIntervalRef.current = null;
                        console.error("Inference failed. Error:", updatedJob.error_message);
                    } else {
                        console.log(`Inference status: ${updatedJob.status}`);
                    }
                } catch (err) {
                    console.error("Error polling inference status:", err);
                    setError(`Failed to poll inference status: ${err.message}. Polling stopped.`);
                    setIsLoading(false);
                    clearInterval(pollingIntervalRef.current); // Stop polling on error
                    pollingIntervalRef.current = null;
                }
            }, 3000); // Poll every 3 seconds

            // Cleanup function: Clear interval when component unmounts or job ID changes
            return () => {
                if (pollingIntervalRef.current) {
                    clearInterval(pollingIntervalRef.current);
                    pollingIntervalRef.current = null;
                }
            };
        }
    }, [currentInferenceJobId, baseApiUrl]); // Re-run effect when currentInferenceJobId or baseApiUrl changes

    // Determine status class for styling
    const getStatusClassName = (status) => {
        switch (status) {        
              
            case 'COMPLETED_INFERENCE': return 'text-green-600 font-semibold';
            case 'FAILED_INFERENCE': return 'text-red-600 font-semibold';
            case 'COMPLETED': return 'text-green-600 font-semibold';
            case 'FAILED': return 'text-red-600 font-semibold';
            case 'QUEUED_INFERENCE':
            case 'RUNNING': 
            case 'INPROGRESS_INFERENCE':
            case 'RUNNING_INFERENCE':
            case 'QUEUED':
            case 'ACCEPTED':
                return 'text-blue-600 font-semibold';
            default: return 'text-gray-600';
        }
    };

    return (
        <div className="inference-container p-6 bg-white rounded-2xl shadow-xl border border-gray-200">
            <button
                onClick={onBack}
                className="back-button mb-6 flex items-center text-blue-600 hover:text-blue-800 font-semibold transition duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 rounded-lg p-2"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Back to Main
            </button>

            <h2 className="text-3xl font-extrabold text-gray-800 mb-4 text-center">
                Model Inference
            </h2>

            <div className="input-section mb-6">
                <label htmlFor="prompt-input" className="block text-lg font-medium text-gray-700 mb-2">
                    Enter your prompt:
                </label>
                <textarea
                    id="prompt-input"
                    className="w-full p-4 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out resize-y text-gray-800"
                    rows="6"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="e.g., Describe a futuristic city powered by renewable energy."
                ></textarea>
                <br />
                <button
                    className="mt-5 w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-lg shadow-md transition duration-200 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-75"
                    onClick={handleSubmitInference}
                    disabled={isLoading || !prompt.trim()}
                >
                    {isLoading ? (
                        <div className="flex items-center justify-center">
                            <svg className="animate-spin h-5 w-5 text-white mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Generating...
                        </div>
                    ) : (
                        'Generate Text'
                    )}
                </button>
            </div>

            {currentInferenceJobId && (
                <div className="job-status-section mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg shadow-sm">
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">Inference Job Status:</h3>
                    <p><strong>Job ID:</strong> {currentInferenceJobId}</p>
                    <p>
                        <strong>Status:</strong>{' '}
                        <span className={getStatusClassName(inferenceStatus)}>{inferenceStatus}</span>
                    </p>
                    {inferenceStatus === 'ACCEPTED' || inferenceStatus === 'QUEUED' || inferenceStatus === 'RUNNING' ? (
                        <p className="text-sm text-gray-500 mt-2">Waiting for inference to complete...</p>
                    ) : null}
                </div>
            )}

            {error && (
                <div className="error-message mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg shadow-sm">
                    <p className="font-bold mb-2">Error:</p>
                    <p>{error}</p>
                </div>
            )}

            {generatedText && (
                <div className="generated-output mt-6 p-5 bg-blue-50 border border-blue-200 rounded-lg shadow-inner">
                    <h3 className="text-xl font-semibold text-blue-800 mb-3">Generated Output:</h3>
                    <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{generatedText}</p>
                </div>
            )}
        </div>
    );
};

// JobStatus Component (remains largely the same, but ensure it uses InferencePage correctly)
const JobStatus = ({ initialJob, apiUrl }) => {
    // Initialize job state with a default empty object to prevent "job is undefined" errors
    const [job, setJob] = useState(initialJob || {}); 
    const intervalRef = useRef(null);
    const [showInferencePage, setShowInferencePage] = useState(false);

    useEffect(() => {
        // Only update job state if initialJob is not null/undefined
        if (initialJob) {
            setJob(initialJob);
        }

        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        const pollStatus = async (currentJobId) => {
            try {
                const response = await axios.get(`${apiUrl}/jobs/${currentJobId}`);
                const updatedJob = response.data;
                setJob(updatedJob);

                if (updatedJob.status !== 'QUEUED' && updatedJob.status !== 'RUNNING') {
                    if (intervalRef.current) {
                        clearInterval(intervalRef.current);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch job status:", error);
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                }
            }
        };

        // Only start polling if initialJob exists and has a status that implies it's ongoing
        if (initialJob && (initialJob.status === 'QUEUED' || initialJob.status === 'RUNNING')) {
            pollStatus(initialJob.id);
            intervalRef.current = setInterval(() => {
                // Ensure job.id is valid before polling
                if (job.id) { // Added check here
                    pollStatus(job.id);
                }
            }, 5000);
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [initialJob, apiUrl, job.id]); // Added job.id to dependencies to ensure pollStatus uses latest ID


    const getStatusClassName = (status) => {
        switch (status) {
            case 'COMPLETED': return 'text-green-600 font-semibold';
            case 'FAILED': return 'text-red-600 font-semibold';
            case 'RUNNING': return 'text-blue-600 font-semibold';
            default: return 'text-gray-600';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4 font-sans">
            <div className="bg-white p-8 rounded-2xl shadow-xl max-w-2xl w-full border border-gray-200">
                {!showInferencePage ? (
                    <div className="status-box">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4 text-center">Finetuning Job Status</h2>
                        {/* Conditionally render job details only if job object exists and has an ID */}
                        {job && job.id ? (
                            <>
                                <p className="mb-2"><strong>Job ID:</strong> {job.id}</p>
                                <p className="mb-2"><strong>Model Name:</strong> {job.new_model_name}</p>
                                <p className="mb-4">
                                    <strong>Status:</strong>{' '}
                                    <span className={getStatusClassName(job.status)}>{job.status}</span>
                                </p>
                                {job.status === 'COMPLETED' && (
                                    <div className="mt-4 p-4 bg-green-50 border border-green-200 text-green-800 rounded-lg shadow-sm">
                                        <p className="font-bold mb-2">Success!</p>
                                        <p>Your model is available at:{' '}</p>
                                        <a
                                            href={`https://huggingface.co/${process.env.REACT_APP_HUGGING_FACE_USERNAME}/Finetuned-${job.new_model_name}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 hover:underline"
                                        >
                                            Hugging Face Hub
                                        </a>
                                        <br />
                                        <button
                                            className="mt-5 w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-75"
                                            onClick={() => setShowInferencePage(true)}
                                        >
                                            Go to Inference Page
                                        </button>
                                    </div>
                                )}
                                {job.status === 'FAILED' && (
                                    <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg shadow-sm">
                                        <p className="font-bold mb-2">Error:</p>
                                        <p>{job.error_message}</p>
                                    </div>
                                )}
                            </>
                        ) : (
                            <p className="text-gray-600 text-center">No finetuning job information available.</p>
                        )}
                    </div>
                ) : (
                    <InferencePage
                        baseApiUrl={apiUrl}
                        base_model={job.base_model}
                        hf_repo={`${process.env.REACT_APP_HUGGING_FACE_USERNAME}/Finetuned-${job.new_model_name}`}
                        onBack={() => setShowInferencePage(false)}
                    />
                )}
            </div>
        </div>
    );
};

export default JobStatus;
