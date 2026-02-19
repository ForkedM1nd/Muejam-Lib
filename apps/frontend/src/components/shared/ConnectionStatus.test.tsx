// ── Connection Status Tests ──
// Tests for connection status indicator component

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConnectionStatus, FloatingConnectionStatus } from './ConnectionStatus';
import { useWebSocketStore } from '@/stores/useWebSocketStore';
import { useOfflineStore } from '@/stores/useOfflineStore';

describe('ConnectionStatus', () => {
    beforeEach(() => {
        // Reset stores before each test
        useWebSocketStore.setState({
            connected: false,
            reconnecting: false,
            connectionState: 'disconnected',
            lastConnectedAt: null,
            reconnectAttempts: 0,
        });

        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [],
        });
    });

    it('should not render when everything is normal', () => {
        // Set normal state
        useWebSocketStore.setState({ connectionState: 'connected', connected: true });
        useOfflineStore.setState({ isOnline: true, queuedRequests: [] });

        const { container } = render(<ConnectionStatus />);
        expect(container.firstChild).toBeNull();
    });

    it('should show offline indicator when offline', () => {
        useOfflineStore.setState({ isOnline: false });

        render(<ConnectionStatus />);
        expect(screen.getByText('Offline')).toBeInTheDocument();
    });

    it('should show queued requests count when offline with showDetails', () => {
        useOfflineStore.setState({
            isOnline: false,
            queuedRequests: [
                { id: '1', url: '/api/test', method: 'POST', timestamp: Date.now(), retryCount: 0 },
                { id: '2', url: '/api/test2', method: 'PUT', timestamp: Date.now(), retryCount: 0 },
            ],
        });

        render(<ConnectionStatus showDetails />);
        expect(screen.getByText('Offline')).toBeInTheDocument();
        expect(screen.getByText('2 updates queued')).toBeInTheDocument();
    });

    it('should show reconnecting state with attempt count in showDetails', () => {
        useWebSocketStore.setState({ connectionState: 'reconnecting', reconnectAttempts: 2 });

        render(<ConnectionStatus showDetails />);
        expect(screen.getByText('Reconnecting')).toBeInTheDocument();
        expect(screen.getByText('Attempt 2...')).toBeInTheDocument();
    });

    it('should show connecting state', () => {
        useWebSocketStore.setState({ connectionState: 'connecting' });

        render(<ConnectionStatus />);
        expect(screen.getByText('Connecting')).toBeInTheDocument();
    });

    it('should show disconnected state', () => {
        useWebSocketStore.setState({ connectionState: 'disconnected' });

        render(<ConnectionStatus />);
        expect(screen.getByText('Disconnected')).toBeInTheDocument();
    });

    it('should show syncing state when connected with queued requests in showDetails', () => {
        useWebSocketStore.setState({ connectionState: 'connected', connected: true });
        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [
                { id: '1', url: '/api/test', method: 'POST', timestamp: Date.now(), retryCount: 0 },
            ],
        });

        render(<ConnectionStatus showDetails />);
        expect(screen.getByText('Syncing')).toBeInTheDocument();
        expect(screen.getByText('Syncing 1 update...')).toBeInTheDocument();
    });

    it('should render compact badge view by default', () => {
        useOfflineStore.setState({ isOnline: false });

        const { container } = render(<ConnectionStatus />);
        // Check for badge class
        expect(container.querySelector('div')).toHaveClass('rounded-full');
        expect(screen.getByText('Offline')).toBeInTheDocument();
    });

    it('should render detailed alert view when showDetails is true', () => {
        useOfflineStore.setState({
            isOnline: false,
            queuedRequests: [
                { id: '1', url: '/api/test', method: 'POST', timestamp: Date.now(), retryCount: 0 },
            ],
        });

        render(<ConnectionStatus showDetails />);
        expect(screen.getByText('Your changes will be synced automatically when connection is restored.')).toBeInTheDocument();
    });

    it('should show singular "update" for single queued request in showDetails', () => {
        useOfflineStore.setState({
            isOnline: false,
            queuedRequests: [
                { id: '1', url: '/api/test', method: 'POST', timestamp: Date.now(), retryCount: 0 },
            ],
        });

        render(<ConnectionStatus showDetails />);
        expect(screen.getByText('1 update queued')).toBeInTheDocument();
    });

    it('should show plural "updates" for multiple queued requests in showDetails', () => {
        useOfflineStore.setState({
            isOnline: false,
            queuedRequests: [
                { id: '1', url: '/api/test', method: 'POST', timestamp: Date.now(), retryCount: 0 },
                { id: '2', url: '/api/test2', method: 'PUT', timestamp: Date.now(), retryCount: 0 },
            ],
        });

        render(<ConnectionStatus showDetails />);
        expect(screen.getByText('2 updates queued')).toBeInTheDocument();
    });
});

describe('FloatingConnectionStatus', () => {
    beforeEach(() => {
        // Reset stores before each test
        useWebSocketStore.setState({
            connected: false,
            reconnecting: false,
            connectionState: 'disconnected',
            lastConnectedAt: null,
            reconnectAttempts: 0,
        });

        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [],
        });
    });

    it('should not render when everything is normal', () => {
        useWebSocketStore.setState({ connectionState: 'connected', connected: true });
        useOfflineStore.setState({ isOnline: true, queuedRequests: [] });

        const { container } = render(<FloatingConnectionStatus />);
        expect(container.firstChild).toBeNull();
    });

    it('should render floating indicator when offline', () => {
        useOfflineStore.setState({ isOnline: false });

        const { container } = render(<FloatingConnectionStatus />);
        const floatingDiv = container.querySelector('.fixed');
        expect(floatingDiv).toBeInTheDocument();
        expect(screen.getByText('Offline')).toBeInTheDocument();
    });

    it('should render with detailed view', () => {
        useOfflineStore.setState({
            isOnline: false,
            queuedRequests: [
                { id: '1', url: '/api/test', method: 'POST', timestamp: Date.now(), retryCount: 0 },
            ],
        });

        render(<FloatingConnectionStatus />);
        expect(screen.getByText('Your changes will be synced automatically when connection is restored.')).toBeInTheDocument();
    });
});
