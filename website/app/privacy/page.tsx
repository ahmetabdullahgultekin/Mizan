import { Shield } from 'lucide-react';
import { ComingSoon } from '@/components/coming-soon';

export const metadata = {
  title: 'Privacy Policy',
  description: 'Privacy policy for the Mizan platform',
};

export default function PrivacyPage() {
  return (
    <ComingSoon
      title="Privacy Policy"
      description="Our commitment to protecting your privacy. Mizan is designed with privacy-first principles - we collect minimal data and never share it with third parties."
      icon={<Shield className="h-10 w-10 text-gold-500" />}
      expectedDate="Q1 2025"
    />
  );
}
