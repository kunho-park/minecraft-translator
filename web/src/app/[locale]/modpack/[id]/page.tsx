import { Link } from "@/i18n/navigation";
import { Search } from "lucide-react";
import Button from "@/components/ui/Button";

// Force dynamic rendering
export const dynamic = "force-dynamic";

export default function ModpackLegacyPage() {
    return (
        <div className="max-w-4xl mx-auto px-4 py-16 text-center animate-fade-in">
            <div className="glass rounded-xl p-8 md:p-16 border border-[var(--border-primary)]">
                <div className="w-24 h-24 bg-[var(--bg-tertiary)] rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
                    <Search className="w-10 h-10 text-[var(--accent-primary)]" />
                </div>
                <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
                    모드팩을 찾을 수 없습니다
                </h1>
                <p className="text-lg text-[var(--text-secondary)] mb-8 max-w-lg mx-auto leading-relaxed">
                    사이트가 개편되어 페이지 주소가 변경되었습니다.
                    <br />
                    아래 버튼을 눌러 모드팩을 다시 검색해주세요.
                </p>
                <Link href="/modpacks">
                    <Button size="lg" className="shadow-lg hover:shadow-xl transition-shadow">
                        모드팩 검색하러 가기
                    </Button>
                </Link>
            </div>
        </div>
    );
}
