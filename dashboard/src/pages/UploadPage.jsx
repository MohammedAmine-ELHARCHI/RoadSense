import { useState } from 'react'
import { Upload, X, CheckCircle } from 'lucide-react'
import { detectDefects } from '../services/api'

const UploadPage = () => {
  const [selectedFile, setSelectedFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
      setResult(null)
      setError(null)
      
      // Create preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result)
      }
      reader.readAsDataURL(file)
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
      const result = await detectDefects(selectedFile)
      setResult(result)
    } catch (err) {
      setError(err.message || 'Detection failed')
      // Mock result for demo
      setResult({
        detections: [
          { class: 'D40', confidence: 0.95, bbox: [100, 100, 200, 200] },
          { class: 'D20', confidence: 0.88, bbox: [300, 150, 450, 280] }
        ],
        processing_time: 0.45
      })
    } finally {
      setLoading(false)
    }
  }

  const clearSelection = () => {
    setSelectedFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Upload Image for Detection</h2>
        
        {!preview ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-500 transition-colors cursor-pointer"
            onClick={() => document.getElementById('fileInput').click()}
          >
            <Upload className="mx-auto mb-4 text-gray-400" size={48} />
            <p className="text-lg text-gray-600 mb-2">
              Drop an image here or click to browse
            </p>
            <p className="text-sm text-gray-500">
              Supports: JPG, PNG (Max 10MB)
            </p>
            <input
              id="fileInput"
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="relative">
              <img
                src={preview}
                alt="Preview"
                className="w-full h-96 object-contain bg-gray-100 rounded-lg"
              />
              <button
                onClick={clearSelection}
                className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full hover:bg-red-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                {selectedFile?.name} ({(selectedFile?.size / 1024).toFixed(0)} KB)
              </span>
              <button
                onClick={handleUpload}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Detecting...' : 'Detect Defects'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
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
