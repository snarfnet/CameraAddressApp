import SwiftUI

struct PhotoPreviewView: View {
    let image: UIImage
    let dismiss: () -> Void

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            Image(uiImage: image)
                .resizable()
                .scaledToFit()
                .ignoresSafeArea()

            VStack {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("PREVIEW")
                            .font(.caption.weight(.black))
                            .foregroundStyle(Color(hex: "67E8F9"))
                        Text("保存した写真")
                            .font(.headline.weight(.heavy))
                            .foregroundStyle(.white)
                    }

                    Spacer()

                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 16, weight: .black))
                            .foregroundStyle(.white)
                            .frame(width: 44, height: 44)
                            .background(.black.opacity(0.5), in: Circle())
                            .overlay(Circle().stroke(.white.opacity(0.16), lineWidth: 1))
                    }
                    .accessibilityLabel("閉じる")
                }
                .padding(.horizontal, 18)
                .padding(.top, 16)

                Spacer()

                HStack(spacing: 10) {
                    Image(systemName: "checkmark.seal.fill")
                        .foregroundStyle(Color(hex: "86EFAC"))
                    Text("住所スタンプ付きで保存済み")
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(.white)
                    Spacer()
                }
                .padding(14)
                .background(.black.opacity(0.58), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(.white.opacity(0.16), lineWidth: 1)
                )
                .padding(.horizontal, 18)
                .padding(.bottom, 18)
            }
        }
    }
}
