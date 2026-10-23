#include "stdafx.h"
#include "AionMovieTracks.h"

namespace NFX {
    CFxContainerGameObject::CFxContainerGameObject() {}
    CFxContainerGameObject::~CFxContainerGameObject() {}
    void CFxContainerGameObject::Update(float fDelta) { (void)fDelta; }
}

CAnimSequenceStringTable::CAnimSequenceStringTable() {}
CAnimSequenceStringTable::~CAnimSequenceStringTable() {}
const char* CAnimSequenceStringTable::GetString(int nIndex) { (void)nIndex; return ""; }

void CCarrierPathInfoTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "CarrierPathInfo"; duration = 0; }
void CDofTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "Dof"; duration = 0; }
void CEffectTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "Effect"; duration = 0; }
void CFxCameraEffectTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "FxCameraEffect"; duration = 0; }
void CFxScreenTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "FxScreen"; duration = 0; }
void CFxTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "Fx"; duration = 0; }
void CGameNarrationTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "GameNarration"; duration = 0; }
void CGameSpeechTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "GameSpeech"; duration = 0; }
void CGameViewTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "GameView"; duration = 0; }
void CHeadRotateTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "HeadRotate"; duration = 0; }
void CImageTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "Image"; duration = 0; }
void CLightTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "Light"; duration = 0; }
void CScreenFxTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "ScreenFx"; duration = 0; }
void CScreenTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "Screen"; duration = 0; }
void CTodControlTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "TodControl"; duration = 0; }
void CVisibleTrack::GetKeyInfo(int key, const char* &desc, float &duration) { desc = "Visible"; duration = 0; }

void InitAionMovieTracks() {
    static NFX::CFxContainerGameObject s_nfxContainer;
    static CAnimSequenceStringTable s_stringTable;
    static CCarrierPathInfoTrack s_carrier;
    static CDofTrack s_dof;
    static CEffectTrack s_effect;
    static CFxCameraEffectTrack s_fxCam;
    static CFxScreenTrack s_fxScreen;
    static CFxTrack s_fxTrack;
    static CGameNarrationTrack s_narration;
    static CGameSpeechTrack s_speech;
    static CGameViewTrack s_gameView;
    static CHeadRotateTrack s_headRotate;
    static CImageTrack s_image;
    static CLightTrack s_light;
    static CScreenFxTrack s_screenFx;
    static CScreenTrack s_screen;
    static CTodControlTrack s_tod;
    static CVisibleTrack s_visible;
}
