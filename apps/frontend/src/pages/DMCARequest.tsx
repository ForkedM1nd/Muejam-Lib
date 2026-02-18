/**
 * DMCA Takedown Request Page
 * 
 * Page for submitting DMCA takedown requests.
 * 
 * Requirements:
 * - 31.1: Provide DMCA takedown request form accessible from footer
 */

import DMCAForm from '@/components/legal/DMCAForm';

export default function DMCARequest() {
    return (
        <div className="container mx-auto py-8 px-4">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">DMCA Takedown Request</h1>
                <p className="text-muted-foreground">
                    If you believe that content on our platform infringes your copyright, you may submit a
                    DMCA takedown request using the form below.
                </p>
            </div>
            <DMCAForm />
        </div>
    );
}
