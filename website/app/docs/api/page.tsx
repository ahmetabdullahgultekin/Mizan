import { Code } from 'lucide-react';
import { ComingSoon } from '@/components/coming-soon';

export const metadata = {
  title: 'API Reference',
  description: 'Complete API reference documentation for the Mizan Core Engine',
};

export default function ApiReferencePage() {
  return (
    <ComingSoon
      title="API Reference"
      description="Complete API documentation with request/response schemas, authentication details, and interactive examples. We're documenting every endpoint to ensure the best developer experience."
      icon={<Code className="h-10 w-10 text-gold-500" />}
      expectedDate="Q1 2025"
    />
  );
}
