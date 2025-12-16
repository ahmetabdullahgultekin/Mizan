import { FileText } from 'lucide-react';
import { ComingSoon } from '@/components/coming-soon';

export const metadata = {
  title: 'Terms of Service',
  description: 'Terms of service for using the Mizan platform',
};

export default function TermsPage() {
  return (
    <ComingSoon
      title="Terms of Service"
      description="Terms and conditions for using the Mizan platform and API. Clear, fair terms that respect both users and contributors."
      icon={<FileText className="h-10 w-10 text-gold-500" />}
      expectedDate="Q1 2025"
    />
  );
}
