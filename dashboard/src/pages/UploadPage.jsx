import { useState } from 'react'
import { Upload, X, CheckCircle, Video, Image as ImageIcon } from 'lucide-react'
import { detectDefects, uploadVideo, getVideoStatus } from '../services/api'

const UploadPage = () => {
  const [uploadType, setUploadType] = useState('image') // 'image' or 'video'
  const [selectedFile, setSelectedFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [videoStatus, setVideoStatus] = useState(null)
  const [processingProgress, setProcessingProgress] = useState(0)

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
      setResult(null)
      setError(null)
      setVideoStatus(null)
      
      // Create preview
      if (uploadType === 'image' && file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onloadend = () => {
          setPreview(reader.result)
        }
        reader.readAsDataURL(file)
      } else if (uploadType === 'video' && file.type.startsWith('video/')) {
        const videoUrl = URL.createObjectURL(file)
        setPreview(videoUrl)
      }
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      const isValidType = uploadType === 'image' 
        ? file.type.startsWith('image/')
        : file.type.startsWith('video/')
      
      if (isValidType) {
        setSelectedFile(file)
        if (uploadType === 'image') {
          const reader = new FileReader()
          reader.onloadend = () => {
            setPreview(reader.result)
          }
          reader.readAsDataURL(file)
        } else {
          const videoUrl = URL.createObjectURL(file)
          setPreview(videoUrl)
        }
      }
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setLoading(true)
    setError(null)

    try {
      if (uploadType === 'image') {
        const result = await detectDefects(selectedFile)
        setResult(result)
      } else {
        // Video upload
        const uploadResult = await uploadVideo(selectedFile)
        setVideoStatus(uploadResult)
        
        // Poll for processing status
        const pollInterval = setInterval(async () => {
          try {
            const status = await getVideoStatus(uploadResult.video_id)
            setVideoStatus(status)
            
            if (status.frames_total > 0) {
              setProcessingProgress((status.frames_extracted / status.frames_total) * 100)
            }
            
            if (status.status === 'COMPLETED' || status.status === 'FAILED') {
              clearInterval(pollInterval)
              setLoading(false)
            }
          } catch (err) {
            clearInterval(pollInterval)
            setError('Failed to get video status')
            setLoading(false)
          }
        }, 2000)
      }
    } catch (err) {
      setError(err.message || 'Upload failed')
      // Mock result for demo
      if (uploadType === 'image') {
        setResult({
          detections: [
            { class: 'D40', confidence: 0.95, bbox: [100, 100, 200, 200] },
            { class: 'D20', confidence: 0.88, bbox: [300, 150, 450, 280] }
          ],
          processing_time: 0.45
        })
      }
    } finally {
      if (uploadType === 'image') {
        setLoading(false)
      }
    }
  }

  const clearSelection = () => {
    setSelectedFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
    setVideoStatus(null)
    setProcessingProgress(0)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Upload Type Selector */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Select Upload Type</h2>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => {
              setUploadType('image')
              clearSelection()
            }}
            className={`p-6 rounded-lg border-2 transition-all ${
              uploadType === 'image'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-blue-300'
            }`}
          >
            <ImageIcon className="mx-auto mb-2" size={32} />
            <p className="font-semibold">Image Upload</p>
            <p className="text-sm text-gray-600 mt-1">Single image detection</p>
          </button>
          <button
            onClick={() => {
              setUploadType('video')
              clearSelection()
            }}
            className={`p-6 rounded-lg border-2 transition-all ${
              uploadType === 'video'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-blue-300'
            }`}
          >
            <Video className="mx-auto mb-2" size={32} />
            <p className="font-semibold">Video Upload</p>
            <p className="text-sm text-gray-600 mt-1">Road inspection video</p>
          </button>
        </div>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">
          Upload {uploadType === 'image' ? 'Image' : 'Video'} for Detection
        </h2>
        
        {!preview ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-500 transition-colors cursor-pointer"
            onClick={() => document.getElementById('fileInput').click()}
          >
            <Upload className="mx-auto mb-4 text-gray-400" size={48} />
            <p className="text-lg text-gray-600 mb-2">
              Drop {uploadType === 'image' ? 'an image' : 'a video'} here or click to browse
            </p>
            <p className="text-sm text-gray-500">
              {uploadType === 'image' 
                ? 'Supports: JPG, PNG (Max 10MB)'
                : 'Supports: MP4, AVI, MOV (Max 500MB)'}
            </p>
            <input
              id="fileInput"
              type="file"
              accept={uploadType === 'image' ? 'image/*' : 'video/*'}
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="relative">
              {uploadType === 'image' ? (
                <img
                  src={preview}
                  alt="Preview"
                  className="w-full h-96 object-contain bg-gray-100 rounded-lg"
                />
              ) : (
                <video
                  src={preview}
                  controls
                  className="w-full h-96 bg-gray-100 rounded-lg"
                />
              )}
              <button
                onClick={clearSelection}
                className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full hover:bg-red-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                {selectedFile?.name} ({(selectedFile?.size / (1024 * 1024)).toFixed(2)} MB)
              </span>
              <button
                onClick={handleUpload}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading 
                  ? (uploadType === 'image' ? 'Detecting...' : 'Processing...') 
                  : (uploadType === 'image' ? 'Detect Defects' : 'Upload & Process')}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Video Processing Status */}
      {videoStatus && uploadType === 'video' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Processing Status</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Status:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                videoStatus.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                videoStatus.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800' :
                videoStatus.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {videoStatus.status}
              </span>
            </div>
            
            {videoStatus.status === 'PROCESSING' && (
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Frames Extracted</span>
                  <span>{videoStatus.frames_extracted || 0} / {videoStatus.frames_total || '?'}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${processingProgress}%` }}
                  />
                </div>
              </div>
            )}

            {videoStatus.status === 'COMPLETED' && (
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Duration:</span>
                  <span className="ml-2 font-semibold">{videoStatus.duration?.toFixed(1)}s</span>
                </div>
                <div>
                  <span className="text-gray-600">FPS:</span>
                  <span className="ml-2 font-semibold">{videoStatus.fps?.toFixed(1)}</span>
                </div>
                <div>
                  <span className="text-gray-600">Resolution:</span>
                  <span className="ml-2 font-semibold">{videoStatus.width}x{videoStatus.height}</span>
                </div>
                <div>
                  <span className="text-gray-600">Frames:</span>
                  <span className="ml-2 font-semibold">{videoStatus.frames_extracted}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Image Detection Results */}
      {result && uploadType === 'image' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-2 mb-4">
            <CheckCircle className="text-green-500" size={24} />
            <h2 className="text-xl font-semibold">Detection Results</h2>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Detections Found:</span>
                <span className="ml-2 font-semibold">{result.detections?.length || 0}</span>
              </div>
              <div>
                <span className="text-gray-600">Processing Time:</span>
                <span className="ml-2 font-semibold">{result.processing_time?.toFixed(2)}s</span>
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="font-semibold mb-3">Detected Defects</h3>
              <div className="space-y-2">
                {result.detections?.map((detection, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <span className="font-semibold">{detection.class}</span>
                      <span className="text-sm text-gray-600 ml-2">
                        ({(detection.confidence * 100).toFixed(0)}% confidence)
                      </span>
                    </div>
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                      Defect {idx + 1}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">
            ⚠️ API connection failed. Showing mock results for demonstration.
          </p>
        </div>
      )}
    </div>
  )
}

export default UploadPage
