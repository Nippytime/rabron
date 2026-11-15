using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>
    /// Small original UI feedback tones. All clips are generated once in
    /// memory; no external media or authored game economy dependencies.
    /// </summary>
    [RequireComponent(typeof(AudioSource))]
    public sealed class PrototypeAudioFeedback : MonoBehaviour
    {
        private const int SampleRate = 24000;
        private AudioSource _output = null!;
        private AudioClip _success = null!;
        private AudioClip _rejected = null!;
        private AudioClip _alarm = null!;

        private void Awake()
        {
            _output = GetComponent<AudioSource>();
            _output.playOnAwake = false;
            _output.loop = false;
            _output.spatialBlend = 0f;
            _output.volume = 0.5f;

            _success = CreateCue("Action accepted", 480f, 760f, 0.16f);
            _rejected = CreateCue("Action rejected", 260f, 160f, 0.22f);
            _alarm = CreateCue("Guard alarm", 760f, 290f, 0.38f);
        }

        public void PlaySuccess() => Play(_success);
        public void PlayRejected() => Play(_rejected);
        public void PlayAlarm() => Play(_alarm);

        private void Play(AudioClip cue)
        {
            // CI's headless Player startup does not depend on audio hardware.
            if (!Application.isBatchMode && cue != null)
                _output.PlayOneShot(cue);
        }

        private static AudioClip CreateCue(string name, float fromHz, float toHz,
                                           float seconds)
        {
            int count = Mathf.CeilToInt(SampleRate * seconds);
            var samples = new float[count];
            float phase = 0f;
            for (int i = 0; i < count; i++)
            {
                float t = i / (count - 1f);
                phase += 2f * Mathf.PI * Mathf.Lerp(fromHz, toHz, t) / SampleRate;
                float envelope = Mathf.Sin(Mathf.PI * t);
                samples[i] = Mathf.Sin(phase) * envelope * envelope * 0.4f;
            }

            AudioClip clip = AudioClip.Create(name, count, 1, SampleRate, false);
            clip.SetData(samples, 0);
            return clip;
        }

        private void OnDestroy()
        {
            if (_success != null)
                Destroy(_success);
            if (_rejected != null)
                Destroy(_rejected);
            if (_alarm != null)
                Destroy(_alarm);
        }
    }
}
