"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { Edit, X, Save, Loader2 } from "lucide-react";
import Button from "@/components/ui/Button";
import { useRouter } from "next/navigation";

interface MapAdminActionsProps {
    map: {
        id: number;
        name: string;
        summary: string;
        author: string | null;
        originalLink: string | null;
        thumbnailUrl: string | null;
    };
}

export default function MapAdminActions({ map }: MapAdminActionsProps) {
    const { data: session } = useSession();
    const router = useRouter();
    const [isEditing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState(false);

    const [formData, setFormData] = useState({
        name: map.name,
        summary: map.summary,
        author: map.author || "",
        originalLink: map.originalLink || "",
    });
    const [thumbnail, setThumbnail] = useState<File | null>(null);

    if (!session?.user?.isAdmin) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const data = new FormData();
            data.append("name", formData.name);
            data.append("summary", formData.summary);
            data.append("author", formData.author);
            data.append("originalLink", formData.originalLink);
            if (thumbnail) {
                data.append("thumbnail", thumbnail);
            }

            const res = await fetch(`/api/maps/${map.id}`, {
                method: "PATCH",
                body: data,
            });

            if (!res.ok) throw new Error("Failed to update map");

            setIsEditing(false);
            router.refresh();
        } catch (error) {
            console.error(error);
            alert("Failed to update map");
        } finally {
            setLoading(false);
        }
    };

    if (isEditing) {
        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                <div className="bg-[var(--bg-card)] rounded-xl p-6 max-w-lg w-full shadow-2xl border border-[var(--border-primary)]">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold text-[var(--text-primary)]">맵 정보 수정</h3>
                        <button onClick={() => setIsEditing(false)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">이름</label>
                            <input
                                type="text"
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)]"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">설명</label>
                            <textarea
                                value={formData.summary}
                                onChange={e => setFormData({ ...formData, summary: e.target.value })}
                                className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] h-24 resize-none"
                                required
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">제작자</label>
                                <input
                                    type="text"
                                    value={formData.author}
                                    onChange={e => setFormData({ ...formData, author: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)]"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">원본 링크</label>
                                <input
                                    type="text"
                                    value={formData.originalLink}
                                    onChange={e => setFormData({ ...formData, originalLink: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)]"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">썸네일 변경</label>
                            <input
                                type="file"
                                accept="image/*"
                                onChange={e => setThumbnail(e.target.files?.[0] || null)}
                                className="w-full text-sm text-[var(--text-secondary)]"
                            />
                        </div>

                        <div className="flex justify-end gap-3 mt-6">
                            <Button type="button" variant="secondary" onClick={() => setIsEditing(false)}>
                                취소
                            </Button>
                            <Button type="submit" disabled={loading}>
                                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                저장
                            </Button>
                        </div>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)} className="w-full">
            <Edit className="w-4 h-4" />
            수정
        </Button>
    );
}
