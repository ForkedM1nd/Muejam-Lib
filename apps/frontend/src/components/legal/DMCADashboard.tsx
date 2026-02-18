import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface DMCARequest {
    id: string;
    copyright_holder: string;
    contact_info: string;
    copyrighted_work_description: string;
    infringing_url: string;
    good_faith_statement: boolean;
    signature: string;
    status: 'PENDING' | 'APPROVED' | 'REJECTED';
    submitted_at: string;
    reviewed_at: string | null;
    reviewed_by: string | null;
}

/**
 * DMCA Agent Dashboard Component
 * 
 * Allows DMCA agents to review and act on takedown requests.
 * 
 * Requirements:
 *   - 31.6: Provide DMCA agent dashboard for reviewing requests
 *   - 31.7: Implement content takedown on approval
 *   - 31.8: Send notification to content author
 */
export const DMCADashboard: React.FC = () => {
    const [requests, setRequests] = useState<DMCARequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<string>('PENDING');
    const [selectedRequest, setSelectedRequest] = useState<DMCARequest | null>(null);
    const [reviewReason, setReviewReason] = useState('');
    const [reviewing, setReviewing] = useState(false);

    useEffect(() => {
        fetchRequests();
    }, [statusFilter]);

    const fetchRequests = async () => {
        try {
            setLoading(true);
            setError(null);

            const params = statusFilter ? { status: statusFilter } : {};
            const response = await axios.get('/api/legal/dmca/requests', { params });

            setRequests(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to load DMCA requests');
        } finally {
            setLoading(false);
        }
    };

    const handleReview = async (requestId: string, action: 'approve' | 'reject') => {
        try {
            setReviewing(true);
            setError(null);

            await axios.post(`/api/legal/dmca/requests/${requestId}/review`, {
                action,
                reason: reviewReason
            });

            // Refresh the list
            await fetchRequests();

            // Close the modal
            setSelectedRequest(null);
            setReviewReason('');

            alert(`Request ${action}d successfully`);
        } catch (err: any) {
            setError(err.response?.data?.error || `Failed to ${action} request`);
        } finally {
            setReviewing(false);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-lg">Loading DMCA requests...</div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-6">DMCA Agent Dashboard</h1>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            {/* Filter Tabs */}
            <div className="mb-6 border-b border-gray-200">
                <nav className="flex space-x-4">
                    {['PENDING', 'APPROVED', 'REJECTED'].map((status) => (
                        <button
                            key={status}
                            onClick={() => setStatusFilter(status)}
                            className={`py-2 px-4 font-medium ${statusFilter === status
                                    ? 'border-b-2 border-blue-500 text-blue-600'
                                    : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            {status}
                        </button>
                    ))}
                </nav>
            </div>

            {/* Requests List */}
            {requests.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                    No {statusFilter.toLowerCase()} requests found.
                </div>
            ) : (
                <div className="space-y-4">
                    {requests.map((request) => (
                        <div
                            key={request.id}
                            className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-xl font-semibold mb-2">
                                        {request.copyright_holder}
                                    </h3>
                                    <p className="text-sm text-gray-500">
                                        Submitted: {formatDate(request.submitted_at)}
                                    </p>
                                    {request.reviewed_at && (
                                        <p className="text-sm text-gray-500">
                                            Reviewed: {formatDate(request.reviewed_at)}
                                        </p>
                                    )}
                                </div>
                                <span
                                    className={`px-3 py-1 rounded-full text-sm font-medium ${request.status === 'PENDING'
                                            ? 'bg-yellow-100 text-yellow-800'
                                            : request.status === 'APPROVED'
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-red-100 text-red-800'
                                        }`}
                                >
                                    {request.status}
                                </span>
                            </div>

                            <div className="space-y-2 mb-4">
                                <div>
                                    <span className="font-medium">Contact Info:</span>{' '}
                                    {request.contact_info}
                                </div>
                                <div>
                                    <span className="font-medium">Infringing URL:</span>{' '}
                                    <a
                                        href={request.infringing_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline"
                                    >
                                        {request.infringing_url}
                                    </a>
                                </div>
                                <div>
                                    <span className="font-medium">Description:</span>
                                    <p className="mt-1 text-gray-700">
                                        {request.copyrighted_work_description}
                                    </p>
                                </div>
                            </div>

                            {request.status === 'PENDING' && (
                                <div className="flex space-x-3">
                                    <button
                                        onClick={() => setSelectedRequest(request)}
                                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                                    >
                                        Review Request
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Review Modal */}
            {selectedRequest && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
                        <h2 className="text-2xl font-bold mb-4">Review DMCA Request</h2>

                        <div className="space-y-4 mb-6">
                            <div>
                                <span className="font-medium">Copyright Holder:</span>{' '}
                                {selectedRequest.copyright_holder}
                            </div>
                            <div>
                                <span className="font-medium">Contact Info:</span>{' '}
                                {selectedRequest.contact_info}
                            </div>
                            <div>
                                <span className="font-medium">Infringing URL:</span>{' '}
                                <a
                                    href={selectedRequest.infringing_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                >
                                    {selectedRequest.infringing_url}
                                </a>
                            </div>
                            <div>
                                <span className="font-medium">Description:</span>
                                <p className="mt-1 text-gray-700">
                                    {selectedRequest.copyrighted_work_description}
                                </p>
                            </div>
                            <div>
                                <span className="font-medium">Signature:</span>{' '}
                                {selectedRequest.signature}
                            </div>
                        </div>

                        <div className="mb-6">
                            <label className="block font-medium mb-2">
                                Reason (optional for approval, recommended for rejection):
                            </label>
                            <textarea
                                value={reviewReason}
                                onChange={(e) => setReviewReason(e.target.value)}
                                className="w-full border border-gray-300 rounded px-3 py-2 h-24"
                                placeholder="Enter reason for your decision..."
                            />
                        </div>

                        {error && (
                            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                                {error}
                            </div>
                        )}

                        <div className="flex space-x-3">
                            <button
                                onClick={() => handleReview(selectedRequest.id, 'approve')}
                                disabled={reviewing}
                                className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50"
                            >
                                {reviewing ? 'Processing...' : 'Approve & Takedown'}
                            </button>
                            <button
                                onClick={() => handleReview(selectedRequest.id, 'reject')}
                                disabled={reviewing}
                                className="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors disabled:opacity-50"
                            >
                                {reviewing ? 'Processing...' : 'Reject'}
                            </button>
                            <button
                                onClick={() => {
                                    setSelectedRequest(null);
                                    setReviewReason('');
                                    setError(null);
                                }}
                                disabled={reviewing}
                                className="px-6 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 transition-colors disabled:opacity-50"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DMCADashboard;
